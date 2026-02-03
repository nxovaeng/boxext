import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

class SecurityScanner(ast.NodeVisitor):
    def __init__(self):
        self.issues = []
        self.current_file = ""

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        self.current_file = str(file_path)
        self.issues = []
        try:
            source = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(source)
            self.visit(tree)
        except Exception as e:
            self.issues.append({
                "file": self.current_file,
                "line": 0,
                "type": "Parse Error",
                "message": str(e)
            })
        return self.issues

    def visit_Call(self, node):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ['eval', 'exec', 'system']:
                self.issues.append({
                    "file": self.current_file,
                    "line": node.lineno,
                    "type": "Critical",
                    "message": f"Usage of dangerous function '{func_name}'"
                })
        
        # Check for subprocess.call, os.system, etc.
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module = node.func.value.id
                method = node.func.attr
                
                if module == 'os' and method in ['system', 'popen', 'remove', 'unlink']:
                     self.issues.append({
                        "file": self.current_file,
                        "line": node.lineno,
                        "type": "High",
                        "message": f"Usage of dangerous os function '{method}'"
                    })
                elif module == 'subprocess':
                     self.issues.append({
                        "file": self.current_file,
                        "line": node.lineno,
                        "type": "High",
                        "message": f"Usage of subprocess module"
                    })
                elif module == 'socket':
                     self.issues.append({
                        "file": self.current_file,
                        "line": node.lineno,
                        "type": "Medium",
                        "message": f"Usage of socket (potential network exfiltration)"
                    })

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ['subprocess', 'socket', 'telnetlib']:
                self.issues.append({
                    "file": self.current_file,
                    "line": node.lineno,
                    "type": "Medium",
                    "message": f"Import of sensitive module '{alias.name}'"
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in ['subprocess', 'socket']:
            self.issues.append({
                "file": self.current_file,
                "line": node.lineno,
                "type": "Medium",
                "message": f"Import from sensitive module '{node.module}'"
            })
        self.generic_visit(node)

class JarSecurityScanner:
    def __init__(self):
        # Signatures for dangerous operations in compiled Java/Dalvik bytecode
        # These are simple string matches for class/method names which usually survive compilation
        self.signatures = [
            (b'java/lang/Runtime', "Possible command execution (Runtime)"),
            (b'ProcessBuilder', "Possible command execution (ProcessBuilder)"),
            (b'dalvik/system/DexClassLoader', "Dynamic Code Loading (DexClassLoader) - Critical Risk"),
            (b'dalvik/system/PathClassLoader', "Dynamic Code Loading (PathClassLoader)"),
            (b'java/net/Socket', "Raw Socket Usage"),
            (b'android/os/Looper', "Suspicious Looper Usage (often used in exploits)"),
            (b'getExternalStorageDirectory', "External Storage Access"),
        ]

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        issues = []
        try:
            # JARs are zip files, but for security scanning we can just grep the binary 
            # content for class names/strings first as a quick heuristic.
            # A full decompiler is too heavy for this environment.
            content = file_path.read_bytes()
            
            for sig, msg in self.signatures:
                if sig in content:
                    issues.append({
                        "file": str(file_path),
                        "line": 0,
                        "type": "High" if "ClassLoader" in str(sig) else "Medium",
                        "message": f"Found suspicious signature: {msg}"
                    })
                    
            # Check for high entropy or obfuscation
            # If we don't find basic Java/Android signatures, it might be packed/encrypted
            if b'java/lang/Object' not in content and b'classes.dex' not in content:
                issues.append({
                    "file": str(file_path),
                    "line": 0,
                    "type": "Warning",
                    "message": "JAR appears packed or encrypted (cannot analyze internals)"
                })
            
        except Exception as e:
            issues.append({
                "file": str(file_path),
                "line": 0,
                "type": "Error",
                "message": f"Failed to scan JAR: {e}"
            })
        return issues

def scan_plugins(directory: Path) -> List[Dict[str, Any]]:
    # 1. Scan Python files
    py_scanner = SecurityScanner()
    # 2. Scan JAR files
    jar_scanner = JarSecurityScanner()
    
    all_issues = []
    
    # Python
    for py_file in directory.rglob('*.py'):
        issues = py_scanner.scan_file(py_file)
        all_issues.extend(issues)
        
    # JAR / DEX
    for jar_file in directory.rglob('*.jar'):
        issues = jar_scanner.scan_file(jar_file)
        all_issues.extend(issues)
        
    # Also scan .dex if they exist (sometimes extracted)
    for dex_file in directory.rglob('*.dex'):
        issues = jar_scanner.scan_file(dex_file)
        all_issues.extend(issues)
        
    return all_issues
