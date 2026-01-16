# ============================================================================
# PARTE 2: COLETA AUTOMÁTICA DO REALWORLD
# ============================================================================

class RealWorldCollector:
    """
    Coleta automaticamente endpoints do FastAPI RealWorld Example App.
    """
    
    def __init__(self, repo_path: str = None):
        """
        Args:
            repo_path: Caminho para o repositório clonado.
                      Se None, clona automaticamente.
        """
        self.repo_path = repo_path
        self.endpoints = []
    
    def clone_repository(self):
        """Clona repositório FastAPI RealWorld se necessário."""
        import subprocess
        
        if self.repo_path is None:
            print("📥 Clonando FastAPI RealWorld Example App...")
            try:
                subprocess.run([
                    "git", "clone",
                    "https://github.com/nsidnev/fastapi-realworld-example-app.git",
                    "temp_realworld"
                ], check=True, capture_output=True)
                self.repo_path = "temp_realworld"
                print("✅ Repositório clonado com sucesso!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erro ao clonar: {e}")
                return False
        return True
    
    def extract_endpoints(self) -> List[Dict[str, Any]]:
        """
        Extrai todos os endpoints dos arquivos de rotas.
        
        Returns:
            Lista de dicionários com informações dos endpoints
        """
        if not self.clone_repository():
            return []
        
        routes_path = Path(self.repo_path) / "app" / "api" / "routes"
        
        if not routes_path.exists():
            print(f"❌ Caminho não encontrado: {routes_path}")
            return []
        
        print(f"📂 Procurando endpoints em: {routes_path}")
        
        for py_file in routes_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            print(f"  📄 Analisando: {py_file.name}")
            
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                endpoints_found = self._parse_endpoints(content, py_file.name)
                self.endpoints.extend(endpoints_found)
        
        print(f"\n✅ Total de endpoints encontrados: {len(self.endpoints)}")
        return self.endpoints
    
    def _parse_endpoints(self, content: str, filename: str) -> List[Dict]:
        """
        Parse endpoints de um arquivo Python.
        
        Returns:
            Lista de endpoints encontrados
        """
        endpoints = []
        
        # Regex para encontrar decoradores @router.{method}
        pattern = r'@router\.(get|post|put|delete|patch)\([^)]*\)(.*?)(?=@router\.|@|class |def \w+\(|$)'
        
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
                route_pattern = r'@router\.\w+\(\s*["\']([^"\']+)["\']'
                route_match = re.search(route_pattern, full_match)
                route = route_match.group(1) if route_match else "unknown"
                
                endpoint = {
                    "id": f"RW_{filename.replace('.py', '').upper()}_{i:02d}",
                    "source": f"realworld/{filename}",
                    "method": method,
                    "route": route,
                    "function_name": function_name,
                    "code": full_match.strip(),
                    "metadata": {
                        "has_async": "async def" in full_match,
                        "has_docstring": '"""' in full_match or "'''" in full_match,
                        "lines": len(full_match.split('\n'))
                    }
                }
                
                endpoints.append(endpoint)
        
        return endpoints
    
    def save_to_json(self, output_path: str = "realworld_endpoints.json"):
        """Salva endpoints coletados em arquivo JSON."""
        data = {
            "metadata": {
                "source": "FastAPI RealWorld Example App",
                "repository": "https://github.com/nsidnev/fastapi-realworld-example-app",
                "collected_at": datetime.now().isoformat(),
                "total_endpoints": len(self.endpoints)
            },
            "endpoints": self.endpoints
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Endpoints salvos em: {output_path}")
        return output_path