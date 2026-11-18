# iPhone Lab — MFA y cierre de sesión, 17/11/2026

El usuario confirmó en el iPhone físico el desafío MFA, el inicio de sesión con la cuenta médica sintética y su cierre.
Se usó el factor existente. El control previo de solo lectura comprobó la cuenta activa, el requisito MFA y el factor activo.
La cuenta médica no tenía familias activas. El transportista tenía una familia activa.

La conciliación terminó con código 0. La familia previa del transportista y la única familia nueva de la cuenta médica
quedaron revocadas en PostgreSQL y ausentes de Redis. Se comprobó un LOGIN y un LOGOUT para la cuenta médica.
La evidencia combina confirmación humana y verificación de servidor. El expediente carece de captura atribuida a este recorrido.
Renovación, expiración y reautenticación conservan sus criterios propios.

Huellas de los recibos privados

- Preflight `4b752a01e75100148fb156813b86c584d60688ed089d6ca9d204ddebe9f19ddc`
- Conciliación `a6c2b8f75f3fb54177b1beb0ff418702d3132691522216f2fac1495727f04d11`
