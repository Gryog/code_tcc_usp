import os
import shutil
import subprocess
from typing import Optional, List, Dict, Any, Iterable
from pathlib import Path
import ast

class TesteRepoCollector:
    """
    Gerencia clonagem e limpeza de repositórios git.
    """
    
    def __init__(self, repo_url: str):
        """
        Args:
            repo_url: URL do repositório git.
        """
        self.repo_url = repo_url
        # Extrai nome do repo da URL (ex: fastapi-realworld-example-app)
        self.repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        self.target_dir = f"temp_repos/{self.repo_name}"
    
    def clone_repository(self) -> Optional[str]:
        """
        Clona o repositório para uma pasta temporária.
        
        Returns:
            Caminho do diretório clonado ou None se falhar.
        """
        # Se já existe, limpa antes
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
        """Remove o diretório clonado."""
        if os.path.exists(self.target_dir):
            print(f"🧹 Limpando diretório temporário: {self.target_dir}")
            try:
                # On Windows, sometimes read-only files prevent deletion. 
                # We can try using a system command or ignoring errors, 
                # but explicit chmod logic is often safer in python, 
                # or just use robust rmtree.
                def remove_readonly(func, path, _):
                    "Clear the readonly bit and reattempt the removal"
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                    
                shutil.rmtree(self.target_dir, onerror=remove_readonly)
            except Exception as e:
                print(f"⚠️ Erro ao limpar diretório: {e}")

    def extract_endpoints(self, search_pattern: str = "**/*.py") -> List[Dict[str, Any]]:
        """
        Extrai todos os endpoints dos arquivos Python do repositório.
        Adaptação da lógica do RealWorldCollector para ser mais genérica.
        
        Args:
            search_pattern: Padrão glob para encontrar arquivos (default: recursive *.py)
            
        Returns:
            Lista de dicionários com informações dos endpoints (id, method, route, code, etc)
        """
        if not os.path.exists(self.target_dir):
            print(f"❌ Diretório não encontrado: {self.target_dir}")
            return []
        
        endpoints = []
        repo_path = Path(self.target_dir)
        
        print(f"📂 Procurando endpoints FastAPI em: {self.target_dir}")
        
        # Ignora pastas comuns de não-codigo ou testes se não for o foco, 
        # mas aqui vamos varrer tudo que bater com o pattern e filtrar por regex
        files = list(repo_path.glob(search_pattern))
        
        print(f"📄 Verificando {len(files)} arquivos Python...")
        
        for py_file in files:
            # Ignora virtuais/configs básicos se desejar
            if ".venv" in str(py_file) or "site-packages" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                found = self._parse_endpoints(content, py_file.name, str(py_file.relative_to(repo_path)))
                if found:
                    endpoints.extend(found)
            except Exception as e:
                print(f"⚠️ Erro ao ler {py_file.name}: {e}")
                
        print(f"✅ Total de endpoints extraídos: {len(endpoints)}")
        return endpoints

    def _parse_endpoints(self, content: str, filename: str, relative_path: str) -> List[Dict]:
        """
        Parse endpoints de um arquivo Python usando Regex.
        
        Args:
            content: Conteúdo do arquivo
            filename: Nome do arquivo
            relative_path: Caminho relativo do arquivo no repo
        """
        endpoints = []
        
        endpoints = self._extract_endpoints_from_ast(
            content=content,
            filename=filename,
            relative_path=relative_path,
        )
        
        return endpoints

    def _extract_endpoints_from_ast(self, content: str, filename: str, relative_path: str) -> List[Dict[str, Any]]:
        allowed_methods = {"get", "post", "put", "delete", "patch"}
        endpoints: List[Dict[str, Any]] = []
        lines = content.splitlines()

        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            print(f"  ⚠️ Erro de sintaxe ao analisar {filename}: {exc}")
            return endpoints

        def iter_functions() -> Iterable[ast.AST]:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield node

        def resolve_base_name(value: ast.AST) -> Optional[str]:
            if isinstance(value, ast.Name):
                return value.id
            if isinstance(value, ast.Attribute):
                return resolve_base_name(value.value)
            return None

        def get_route_from_call(call: ast.Call) -> str:
            if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                return call.args[0].value
            for keyword in call.keywords:
                if keyword.arg in {"path", "url"} and isinstance(keyword.value, ast.Constant):
                    if isinstance(keyword.value.value, str):
                        return keyword.value.value
            return "unknown"

        endpoint_index = 0
        for func_node in iter_functions():
            decorators = func_node.decorator_list
            matched = None
            for decorator in decorators:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr
                if method not in allowed_methods:
                    continue
                base_name = resolve_base_name(decorator.func.value)
                if base_name not in {"router", "app"}:
                    continue
                matched = (method, decorator)
                break

            if not matched:
                continue

            endpoint_index += 1
            method, decorator_call = matched
            function_name = func_node.name
            route = get_route_from_call(decorator_call)

            start_line_candidates = [func_node.lineno]
            for dec in decorators:
                if hasattr(dec, "lineno"):
                    start_line_candidates.append(dec.lineno)
            start_line = max(min(start_line_candidates) - 1, 0)
            end_line = func_node.end_lineno - 1 if func_node.end_lineno else func_node.lineno
            snippet = "\n".join(lines[start_line:end_line + 1]).strip()

            clean_name = filename.replace(".py", "").replace(".", "_").upper()
            endpoint_id = f"{self.repo_name.upper()}_{clean_name}_{function_name}_{endpoint_index}"

            endpoints.append(
                {
                    "id": endpoint_id,
                    "source": relative_path,
                    "method": method.upper(),
                    "route": route,
                    "function_name": function_name,
                    "code": snippet,
                    "metadata": {
                        "has_async": isinstance(func_node, ast.AsyncFunctionDef),
                        "lines": len(snippet.split("\n")) if snippet else 0,
                    },
                }
            )

        return endpoints

