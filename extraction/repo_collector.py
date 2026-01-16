import os
import shutil
import subprocess
import ast
from typing import Optional, List, Dict, Any, Set, Tuple
from pathlib import Path

class RepoCollector:
    """
    Gerencia clonagem de repositórios git e extração de endpoints via AST.
    """
    
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        self.target_dir = f"temp_repos/{self.repo_name}"
        self._module_map = {} # Cache de resolução de módulos

    def clone_repository(self) -> Optional[str]:
        if os.path.exists(self.target_dir):
            self.cleanup()
            
        print(f"📥 Clonando {self.repo_name}...")
        try:
            subprocess.run([
                "git", "clone",
                self.repo_url,
                self.target_dir
            ], check=True, capture_output=True)
            print(f"✅ Repositório clonado em: {self.target_dir}")
            return self.target_dir
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao clonar {self.repo_name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Erro inesperado ao clonar: {e}")
            return None
    
    def cleanup(self):
        if os.path.exists(self.target_dir):
            print(f"🧹 Limpando diretório temporário: {self.target_dir}")
            try:
                def remove_readonly(func, path, _):
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(self.target_dir, onerror=remove_readonly)
            except Exception as e:
                print(f"⚠️ Erro ao limpar diretório: {e}")

    def extract_endpoints(self) -> List[Dict[str, Any]]:
        """
        Extrai endpoints usando análise estática (AST).
        1. Encontra instâncias de FastAPI.
        2. Rastreia include_router.
        3. Extrai rotas de apps e routers.
        """
        if not os.path.exists(self.target_dir):
            print(f"❌ Diretório não encontrado: {self.target_dir}")
            return []

        endpoints = []
        repo_path = Path(self.target_dir)  
        
        print(f"� Indexando arquivos Python em {self.target_dir}...")
        self._build_module_map(repo_path)
        
        # 1. Encontrar Entry Points (arquivos que instanciam FastAPI)
        entry_points = self._find_entry_points(repo_path)
        if not entry_points:
            print("⚠️ Nenhuma instância de FastAPI() encontrada. Tentando fallback para 'main.py' ou 'app.py' genérico...")
            # Fallback simples se não achar a instanciação explícita
            possible = list(repo_path.glob("**/main.py")) + list(repo_path.glob("**/app.py"))
            entry_points = [(p, "app") for p in possible] # Chute: variável chama 'app'

        print(f"� Entry points encontrados: {len(entry_points)}")

        processed_files = set()
        # Fila de processamento: (caminho_arquivo, [lista_de_vars_router_ou_app])
        # Começamos com os entry points e a variável do app (ex: 'app')
        queue = [(path, {var_name}) for path, var_name in entry_points]

        while queue:
            current_file, router_vars = queue.pop(0)
            if current_file in processed_files:
                continue
            
            processed_files.add(current_file)
            
            try:
                with open(current_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                rel_path = str(current_file.relative_to(repo_path))
                
                # 2. Extrair Endpoints deste arquivo para as variáveis conhecidas
                visitor = EndpointVisitor(source, router_vars, rel_path, self.repo_name)
                visitor.visit(tree)
                endpoints.extend(visitor.found_endpoints)
                
                # 3. Descobrir novos arquivos via include_router
                # Procuramos chamadas do tipo: app.include_router(api_router, ...)
                # Ou router.include_router(other_router, ...)
                if router_vars:
                    includes = self._find_includes(tree, router_vars, source)
                    for included_var_name in includes:
                        target_var_look = included_var_name
                        base_module_var = included_var_name
                        
                        if '.' in included_var_name:
                             parts = included_var_name.split('.')
                             base_module_var = parts[0]
                             target_var_look = parts[1]

                        origin = self._resolve_variable_origin(tree, current_file, base_module_var)
                        
                        if origin:
                            target_file, resolved_name = origin
                            
                            final_target_var = target_var_look
                            if '.' not in included_var_name:
                                final_target_var = resolved_name

                            if resolved_name is None:
                                final_target_var = target_var_look

                            queue.append((target_file, {final_target_var}))

            except Exception as e:
                print(f"⚠️ Erro ao processar {current_file}: {e}")

        print(f"✅ Total de endpoints extraídos (AST): {len(endpoints)}")
        return endpoints

    def _build_module_map(self, root: Path):
        """Mapeia nomes de módulos python para caminhos de arquivo."""
        self._module_map = {}
        for path in root.glob("**/*.py"):
            rel = path.relative_to(root)
            # a/b/c.py -> a.b.c
            parts = list(rel.parts)
            parts[-1] = parts[-1].replace('.py', '')
            if parts[-1] == '__init__':
                parts = parts[:-1]
            if parts:
                module_name = ".".join(parts)
                self._module_map[module_name] = path

    def _find_entry_points(self, root: Path) -> List[Tuple[Path, str]]:
        """Busca arquivos que fazem 'app = FastAPI(...)'."""
        found = []
        for path in root.glob("**/*.py"):
            try:
                res = self._scan_for_fastapi_instance(path)
                if res:
                    found.append((path, res))
            except:
                continue
        return found

    def _scan_for_fastapi_instance(self, path: Path) -> Optional[str]:
        """Lê arquivo e retorna nome da variável se instanciar FastAPI."""
        with open(path, 'r', encoding='utf-8') as f:
            if "FastAPI" not in f.read(): # Fast check
                return None
            f.seek(0)
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    # Checa FastAPI() ou xxx.FastAPI()
                    is_fastapi = False
                    if isinstance(func, ast.Name) and func.id == "FastAPI":
                        is_fastapi = True
                    elif isinstance(func, ast.Attribute) and func.attr == "FastAPI":
                        is_fastapi = True
                    
                    if is_fastapi:
                        # Pega o nome da variável (considerando apenas atribuição simples)
                        if node.targets and isinstance(node.targets[0], ast.Name):
                            return node.targets[0].id
        return None

    def _find_includes(self, tree: ast.AST, known_parents: Set[str], source: str) -> Set[str]:
        """Encontra variáveis incluídas via include_router usando as variáveis pai conhecidas."""
        included = set()
        
        def get_full_name(node):
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                value = get_full_name(node.value)
                if value:
                    return f"{value}.{node.attr}"
            return None

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "include_router":
                    caller = node.func.value
                    caller_id = get_full_name(caller)
                    
                    # print(f"   [Includes] Checking caller: {ast.dump(caller)} -> ID: {caller_id}")
                    
                    if caller_id and caller_id in known_parents:
                         if node.args:
                            arg0 = node.args[0]
                            full_name = get_full_name(arg0)
                            if full_name:
                                included.add(full_name)
                                # print(f"     -> Found include: {full_name}")
                            # else:
                                # print(f"     -> Arg0 not parsable: {ast.dump(arg0)}")
        return included

    def _resolve_variable_origin(self, tree: ast.AST, current_file: Path, var_name: str) -> Optional[Tuple[Path, Optional[str]]]:
        """
        Descobre onde 'var_name' foi definido dentro do 'tree' (no 'current_file').
        Retorna (arquivo_origem, nome_variavel_origem).
        Se nome_variavel_origem for None, indica que o arquivo é o próprio módulo referenciado por var_name.
        """
        # 1. Checar Imports
        # from X import Y as var_name
        # from X import var_name
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    # Se alias.asname == var_name OU (alias.asname is None e alias.name == var_name)
                    target_alias = alias.asname if alias.asname else alias.name
                    if target_alias == var_name:
                        # Achou a origem!
                        orig_name = alias.name
                        # Resolver modulo
                        resolved_path = self._resolve_import_path(current_file, module, node.level)
                        
                        if resolved_path:
                             # Check if it was a submodule import (e.g. imports 'api' which is api.py inside package)
                             if resolved_path.name == '__init__.py':
                                 candidate_sub = resolved_path.parent / f"{orig_name}.py"
                                 if candidate_sub.exists():
                                     return (candidate_sub, None)
                                 candidate_pkg = resolved_path.parent / orig_name / "__init__.py"
                                 if candidate_pkg.exists():
                                     return (candidate_pkg, None)

                             return (resolved_path, orig_name)
        
        # 2. Checar Atribuição Local
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                 if node.targets and isinstance(node.targets[0], ast.Name):
                     if node.targets[0].id == var_name:
                         return (current_file, var_name)

        return None

    def _resolve_import_path(self, current_file: Path, module: str, level: int) -> Optional[Path]:
        """
        Resolve caminho físico de um import.
        current_file: path completo do arquivo que tem o import
        module: string do modulo (ex: 'core.config' ou None se for relativo puro)
        level: quantidade de pontos (0=absoluto, 1=. , 2=..)
        """
        root = Path(self.target_dir)
        
        if level > 0:
            # Relativo
            # level 1 (.): mesmo dir
            # level 2 (..): pai
            base_dir = current_file.parent
            for _ in range(level - 1):
                base_dir = base_dir.parent
            
            if module:
                 # from .sub import x -> module='sub'
                 parts = module.split('.')
                 target = base_dir.joinpath(*parts)
            else:
                 # from . import x
                 target = base_dir
            
            # Tenta .py
            candidate = target.with_suffix('.py')
            if candidate.exists():
                return candidate
            
            # Tenta pacote (__init__.py)
            candidate_pkg = target / "__init__.py"
            if candidate_pkg.exists():
                return candidate_pkg
                
        else:
            # Absoluto (dentro do projeto)
            # module: 'app.api.users'
            # Tenta map
            if not module: return None
            
            # Tente exato
            if module in self._module_map:
                return self._module_map[module]
            
            # Tenta parciais (as vezes o map não pegou ou é pacote)
            parts = module.split('.')
            candidate = root.joinpath(*parts).with_suffix('.py')
            if candidate.exists():
                 return candidate
            
            candidate_pkg = root.joinpath(*parts) / "__init__.py"
            if candidate_pkg.exists():
                 return candidate_pkg
                 
        return None


class EndpointVisitor(ast.NodeVisitor):
    def __init__(self, source_code: str, target_vars: Set[str], relative_path: str, repo_name: str):
        self.source_code = source_code
        self.target_vars = target_vars # variaveis que são routers ou app
        self.relative_path = relative_path
        self.repo_name = repo_name
        self.found_endpoints = []
        
    def visit_FunctionDef(self, node):
        # Wraps sync funcs
        self._check_endpoint(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        # Wraps async funcs
        self._check_endpoint(node)
        self.generic_visit(node)
        
    def _check_endpoint(self, node):
        # Verifica decoradores
        is_endpoint = False
        method = "UNKNOWN"
        route = ""
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                # @app.get("/foo")
                if isinstance(decorator.func, ast.Attribute):
                    # Checa se o objeto do atributo (o 'app' em app.get) está nas nossas variaveis alvo
                    obj = decorator.func.value
                    if isinstance(obj, ast.Name) and obj.id in self.target_vars:
                        # É um router/app que estamos rastreando!
                        attr = decorator.func.attr
                        if attr in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                            is_endpoint = True
                            method = attr.upper()
                            # Tenta pegar a rota (primeiro arg)
                            if decorator.args:
                                arg0 = decorator.args[0]
                                if isinstance(arg0, ast.Constant): # python 3.8+
                                    route = arg0.value
                                elif isinstance(arg0, ast.Str): # python < 3.8
                                    route = arg0.s
                            break
        
        if is_endpoint:
            self._add_endpoint(node, method, route)
            
    def _add_endpoint(self, node, method, route):
        code_segment = ast.get_source_segment(self.source_code, node)
        
        # ID único
        clean_name = self.relative_path.replace('.py', '').replace('.', '_').replace('/', '_').upper()
        func_name = node.name
        idx = len(self.found_endpoints)
        endpoint_id = f"{self.repo_name.upper()}_{clean_name}_{func_name}_{idx}"
        
        self.found_endpoints.append({
            "id": endpoint_id,
            "source": self.relative_path,
            "method": method,
            "route": route, # Nota: rota relativa ao router. A composição completa exigiria stack de prefixos.
            "function_name": func_name,
            "code": code_segment,
            "metadata": {
                "has_async": isinstance(node, ast.AsyncFunctionDef),
                "lines": code_segment.count('\n') + 1 if code_segment else 0
            }
        })
