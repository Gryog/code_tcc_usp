import os
import shutil
import subprocess
from typing import Optional, List, Dict, Any
import re
from pathlib import Path

class RepoCollector:
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
        
        print(f"  📄 Verificando {len(files)} arquivos Python...")
        
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
                print(f"  ⚠️ Erro ao ler {py_file.name}: {e}")
                
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
        
        # Regex ajustado para pegar @router.method ou @app.method
        # RealWorld usa @router, mas vamos tentar ser um pouco mais flexíveis se possível,
        # ou manter estrito conforme solicitado "parecido com RealWorldCollector".
        # O padrão original era: r'@router\.(get|post|put|delete|patch)\([^)]*\)(.*?)(?=@router\.|@|class |def \w+\(|$)'
        # Vamos permitir router ou app
        pattern = r'@(?:router|app)\.(get|post|put|delete|patch)\([^)]*\)(.*?)(?=@(?:router|app)\.|@|class |def \w+\(|$)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for i, match in enumerate(matches, 1):
            method = match.group(1).upper()
            full_match = match.group(0)
            
            # Extrai a função
            func_pattern = r'(async\s+)?def\s+(\w+)\s*\([^)]*\)'
            func_match = re.search(func_pattern, full_match)
            
            if func_match:
                function_name = func_match.group(2)
                
                # Extrai rota
                route_pattern = r'@(?:router|app)\.\w+\(\s*["\']([^"\']+)["\']'
                route_match = re.search(route_pattern, full_match)
                route = route_match.group(1) if route_match else "unknown"
                
                # ID único para o endpoint
                clean_name = filename.replace('.py', '').replace('.', '_').upper()
                endpoint_id = f"{self.repo_name.upper()}_{clean_name}_{function_name}_{i}"
                
                endpoint = {
                    "id": endpoint_id,
                    "source": relative_path,
                    "method": method,
                    "route": route,
                    "function_name": function_name,
                    "code": full_match.strip(),
                    "metadata": {
                        "has_async": "async def" in full_match,
                        "lines": len(full_match.split('\n'))
                    }
                }
                
                endpoints.append(endpoint)
        
        return endpoints

