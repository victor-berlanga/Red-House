# Plan de verificación en Windows 11

Pendiente de ejecución. El workflow configura Windows Server 2025 x64 para construcción y smoke; no demuestra operación en Windows 11 ni sustituye la revisión visual.

En una máquina Windows 11 x64 autorizada, instalar Python 3.12 y usar una copia limpia del repositorio. En PowerShell, desde `apps/desktop`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt pytest==9.1.1
.\.venv\Scripts\python.exe sync_contracts.py --check
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest tests --ignore-glob='*_lab.py' -q
cmd /c build.bat
.\.venv\Scripts\python.exe -c "import subprocess; subprocess.run([r'dist\RedHouse\RedHouse.exe', '--smoke-report', 'package-smoke.json'], check=True, timeout=45)"
Get-Content .\package-smoke.json
Remove-Item Env:QT_QPA_PLATFORM
```

Registrar versión exacta de Windows, arquitectura, Python, dependencias y SHA-256 del paquete; confirmar `ok: true` y que los contratos pertenecen al mismo commit. El lock completo disponible corresponde a macOS x86_64; resolver y fijar las transitivas Windows antes de declarar una construcción reproducible allí. La ejecución de CI y su artefacto requieren un runner disponible; no se ha lanzado esta ejecución.

Con un laboratorio HTTPS aislado y certificado confiable, probar en ventana visible inicio de sesión y MFA si aplica, inventario y detalle, alta y recuperación de respuesta perdida, permisos, cierre de sesión y acceso al almacén seguro de Windows. Revisar capturas reales a tamaño compacto y normal. Verificar recuperación tras terminar y reiniciar el proceso sin registrar contraseñas, JWT ni comprobantes. Añadir pruebas de impresora o lector solo si existen periféricos; una vista previa no acredita impresión física. Anotar fallos y límites en evidencia antes de declarar soporte.
