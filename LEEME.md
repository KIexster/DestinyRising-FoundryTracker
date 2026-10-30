# Foundry Tracker 0.2 — Armería — Destiny Rising Global

Abre FoundryTracker_Armeria.exe con MuMu y tu personaje de Destiny Rising Global conectados. La aplicación busca el juego y lee tus contadores automáticamente. La primera lectura puede tardar entre 20 y 60 segundos en el equipo donde se probó; el tiempo depende del emulador. No requiere instalar Python ni ADB por separado.

## Funciones

- Siete desafíos, cada uno con su emblema: Exotic Enthusiast, Riviks & Wright, Novak, Strid, Jiangshi Steelworks I/II y Eclipse Monolith.
- Bajas guardadas por ID de arma, bajas restantes hasta 1.000 y progreso del logro sobre 8.
- Búsqueda por nombre/ID, filtro por colección y solo pendientes; ordenación por encabezados.
- Botón de actualización y actualización opcional 60 segundos después de finalizar cada lectura.
- Exportación manual a CSV o JSON.

“Sin registro” indica que el mapa del juego no contenía ese ID, no un cero medido. Los contadores se agrupan por ID de diseño, no por roll o copia individual. El catálogo contiene 117 definiciones vinculadas a las seis colecciones; no implica que todas sigan obtenibles.

## Compatibilidad de esta primera versión

- Windows de 64 bits; probado en el MuMu actual del usuario.
- Paquete global com.netease.g108na y build de recursos 202610280026.
- ADB y acceso root de MuMu disponibles. El lector no activa root ni cambia la configuración del emulador.
- Se reutilizan los dispositivos ADB conectados; si no hay ninguno, se intenta conectar al puerto local habitual 127.0.0.1:16384. Si el puerto de MuMu es distinto, conecta esa instancia desde sus herramientas ADB antes de abrir el lector.
- Si hay varias sesiones del juego abiertas, deja solo la que quieres consultar. No se elige una cuenta al azar.

Una huella del encabezado del motor y la build de recursos identifican la build verificada. Con una build desconocida el lector busca el intérprete en memoria y sigue en modo «sin verificar»: solo muestra el resultado si todos los logros cuadran con las bajas de sus armas, y cualquier error de estructura se convierte en el aviso de descargar la última versión. Los desplazamientos están en la sección `engine` de catalog.json y se pueden sobrescribir con `%APPDATA%\FoundryTracker\engine.json`. No se promete compatibilidad con CN, teléfonos físicos u otros emuladores/builds.

## Lectura y archivos

El programa lee memoria del proceso a través de ADB. No escribe memoria, inyecta código, llama métodos del juego ni desbloquea logros: muestra el progreso que ya tiene el personaje. No extrae tokens, no modifica certificados, no consulta la API de NetEase ni envía los datos a terceros. Las únicas conexiones de ADB utilizadas son locales al emulador.

El ejecutable incluye un catálogo de armas, no datos privados de la cuenta ni direcciones de la sesión original. Localiza el intérprete, el personaje y sus propiedades de nuevo cada vez. Los datos mostrados se mantienen en memoria y solo se guardan si eliges exportarlos. El empaquetador extrae temporalmente Python/Tk/ADB para ejecutar el programa.

Una nueva lectura oculta los resultados anteriores hasta validar la sesión actual. Si detecta un reinicio o cambio de personaje durante la lectura, descarta el resultado. Una discrepancia entre las armas sobre 1.000 bajas y el contador del logro aparece en la barra de estado para revisarla.

## Verificación realizada

- Cuatro pruebas de manejo de errores: juego ausente, varias sesiones, motor incompatible y mapa cíclico.
- Lectura desde Python sin direcciones guardadas: 106 contadores, siete logros coincidentes.
- Lectura desde el ejecutable empaquetado: 106 contadores; Riviks & Wright 2/8 y Eclipse Monolith 3/8, otros cuatro 0/8.
- Revisión de interfaz y filtros. No se jugaron partidas ni se alteraron logros para hacer la prueba.

Los resultados anteriores describen la cuenta y el momento de la prueba, no valores incluidos en el programa. Esta versión no tiene firma digital.

## Código fuente

src/app.py: entrada. src/gallery.py: galería de emblemas y detalle por colección. src/tracker.py: detección, validación y extracción. src/memory_reader.py: lectura acotada de estructuras. src/catalog.json: catálogo y huella de compatibilidad. test_tracker.py: pruebas de errores.

Para recompilar, usa Python 3.12 con Tk y ejecuta build.ps1 (con `-Python <ruta>` eliges el intérprete). Crea `.venv-build` con las herramientas fijadas en requirements-build.txt, pasa los tests y deja en dist el .exe, su SHA-256 y el zip de la release, con el nombre de la versión de src/resources.py. Los tres binarios de ADB deben estar en src/adb. No hace falta ejecutar prepare.py: es una herramienta interna para generar la huella y el catálogo desde los materiales de investigación.

## Interfaz 0.2

Pulsa un emblema para abrir su colección. Las pestañas Todas / Completadas / Pendientes filtran solo ese logro. La cabecera muestra progreso sobre 8, total de armas completadas y pendientes del catálogo, y el arma con contador conocido más cercana a 1.000. Usa Todos los emblemas para volver. Los nombres de armas y logros se mantienen en inglés para coincidir con el juego; la navegación está en español. La exportación CSV desde una colección incluye solo esa colección; JSON conserva la lectura completa.

Los siete emblemas se extrajeron de los recursos originales. El emblema repetido en las referencias no crea un logro adicional. No se incluyen tres desafíos sin entrada publicada actual en AchievementData.

## Interfaz 0.4

- Selector de idioma ES / EN en la esquina superior derecha. Cambia toda la interfaz al instante, incluidos los mensajes del lector, y se recuerda en `%APPDATA%\FoundryTracker\settings.json`. La primera vez arranca en inglés. Los nombres de armas y logros siguen en inglés, como en el juego.
- Animaciones:
  - Entrada escalonada de los emblemas y relleno progresivo de los 8 indicadores de cada logro.
  - Brillo dorado pulsante en los logros completados y realce al pasar el cursor.
  - Barrido azul en los indicadores mientras se lee el juego.
  - Transición deslizante al abrir una colección, contadores que suben hasta su valor y anillo de progreso alrededor del emblema.
  - Barras de progreso hacia 1.000 bajas en cada arma, que se rellenan fila a fila.
- La tabla se sustituyó por una lista con barra de progreso y etiqueta de estado. La ordenación por encabezados se mantiene: el ▲/▼ indica la columna activa.
- Atajos: F5 o Ctrl+R actualizan; Esc vuelve a los emblemas.
- `FoundryTracker_Armeria.exe --demo lectura.json` abre la interfaz con una exportación JSON en lugar de leer el juego. Sirve para revisar el diseño sin MuMu.

Solo cambió src/gallery.py: el lector (tracker.py y memory_reader.py) es el mismo de la 0.3. La interfaz 0.3 se conserva en gallery_v03_backup.py.

## Interfaz 0.5

- Paleta negro y dorado. Los logros y armas completados usan un dorado claro sólido; las armas en progreso, un dorado bronce.
- Intro al abrir: aparece el emblema dorado de los lobos, se ilumina una línea dorada por el centro y se abre en dos mitades como una puerta para mostrar el programa. Dura unos 2 segundos. Un clic sobre el emblema la abre al momento. `--no-intro` la omite.
- Las dos mitades están en src/emblems/splash_left.png y splash_right.png, generadas desde Imagenes_editadas/iron_banner_negro_dorado.png.

- 0.5.1: el marco de la tarjeta ya no se corta al pasar el cursor; solo se eleva el contenido.
- 0.5.2: el círculo de fondo del emblema ya no toca el marco al pasar el cursor; en tarjetas bajas se reduce y el contenido se compacta.

## Interfaz 0.6

- Imágenes de las armas:
  - Miniatura en cada fila de la lista.
  - Panel lateral al hacer clic en un arma: render grande, colección, bajas, bajas restantes, barra de progreso animada y porcentaje.
  - Miniatura en la línea «Próxima meta»; un clic sobre ella abre su panel.
- El panel se cierra con ✕ o Esc; un segundo Esc vuelve a los emblemas. El arma abierta queda marcada en dorado en la lista.
- Las imágenes van en src/weapons (117 armas, unos 6 MB): {id}_s.png de 48 px y {id}_l.png de hasta 420×165. Se generan con prepare_weapon_images.py a partir de ../Assets/Weapons. La variante aw03s03t01 usa el arte de The Jade Rabbit (aw03s03). build.ps1 ya incluye la carpeta.

## Interfaz 0.7

- **Historial y sesión.** Cada lectura válida se guarda en `%APPDATA%\FoundryTracker\history.json` (solo las bajas por ID de arma, últimas 200 lecturas). Cada arma muestra «+N» con lo ganado desde la lectura anterior. «Iniciar sesión» fija un punto de partida: hasta «Terminar sesión», el botón y las armas muestran lo ganado en la sesión, y al terminar aparece el resumen. Las tarjetas de los emblemas muestran las bajas ganadas en esa colección.
- **Camino más corto.** Para cada logro se calcula el mínimo de bajas para llegar a 8/8 con las armas pendientes más avanzadas. Las armas sin registro cuentan como 1.000. Aparece en cada tarjeta («faltan N bajas»), arriba a la derecha («Más cerca: …») y en la colección, con las armas elegidas marcadas con una barra dorada.
- **Compartir.** Genera una imagen PNG de 1200×720 en negro y dorado, con el emblema de los lobos, los 7 logros y su progreso (`sharecard.py`, Pillow).
- **Aviso de root.** Al abrir, después de la intro, recuerda activar el permiso de root en MuMu Player. Puede ocultarse con «No volver a mostrar». La explicación de los términos del juego está al final de GITHUB_README.md.
- **Nitidez.** El programa declara compatibilidad con el escalado de Windows. Los lienzos se dibujan en unidades de 96 ppp y se escalan, así que en pantallas al 125 % o 150 % se ven nítidos y con las mismas proporciones. Por encima del 130–140 % usa los emblemas de 128 px y miniaturas de arma de 72 px.
- **Actualización necesaria.** Si una build nueva no se puede leer con seguridad, en lugar del error técnico aparece en dorado un aviso que pide descargar la última versión.
- **Traducciones en archivos.** Los textos están en `src/lang/*.json` (`label`, `thousands`, `strings` y la traducción de los mensajes del lector). Para añadir un idioma basta con copiar `en.json` con otro nombre; el selector lo muestra solo.
- **Código separado.** `theme.py` (colores y medidas), `widgets.py`, `cards.py`, `weapons.py`, `history.py`, `sharecard.py`, `i18n.py`, `resources.py` y `gallery.py` (ventana principal). El lector (`tracker.py`, `memory_reader.py`) no cambió.
- 0.7.1: icono propio (emblema dorado de los lobos) en la ventana, la barra de tareas y el .exe, en lugar de la pluma de Tk. Se genera con prepare_icon.py en src/emblems/app_icon.ico.
- 0.7.2: MuMu puede aparecer dos veces en adb (`emulator-5554` y `127.0.0.1:16384`). El lector agrupa los dispositivos por `boot_id`, así que esa duplicación ya no da el aviso de «varias sesiones»; dos emuladores distintos con el juego abierto lo siguen dando.
- 0.7.3: ADB se copia a `%LOCALAPPDATA%\FoundryTracker\adb` y usa su propio puerto (5041) en lugar del 5037 que comparte con MuMu; al cerrar la ventana se detiene ese servidor (`adb_runtime.py`). Antes el servidor seguía en marcha desde la carpeta temporal `_MEI…` del .exe e impedía borrarla. Compilación reproducible: build.ps1 instala las versiones fijadas de requirements-build.txt, pasa los tests, compila sin UPX y genera el .exe, el SHA-256 y el zip con el nombre de la versión.
- 0.8.0: builds nuevas del juego. `Session.locate()` busca `_PyRuntime` (cabecera de CPython 3.12: `1,0,1,1,1`, intérprete principal = primero de la lista, contador pequeño) en los datos escribibles de libGame.so y en su .bss, empezando junto al desplazamiento conocido, y lo valida con `interp->runtime` y el diccionario de módulos; la posición encontrada se guarda por huella en settings.json (`runtime_offsets`). Una build o huella desconocida ya no se rechaza: se lee como «sin verificar», exige coherencia total entre logros y armas y convierte los errores de estructura (`StructureError`) en el aviso de actualización. Los desplazamientos del intérprete y la cadena personaje → tabla de propiedades pasan a la sección `engine` de catalog.json, sobrescribible con `%APPDATA%\FoundryTracker\engine.json` (también `expected_patch` y `engine_header_sha256`).
- 0.8.1: lecturas más rápidas. Casi todo el tiempo se iba en idas y vueltas de una página por el canal de adb (674 de unos 23 ms). `FastReader.gather()` pide páginas sueltas en lotes (las consecutivas comparten un `dd`), `read()` pide de una vez todas las páginas seguidas que le faltan y `span_of()` busca la región con bisect. `module()` lee los nombres de módulo de 64 en 64 y para en el primero que coincide; la verificación final compara punteros (`attr_keys`) en vez de releer cada nombre. Cada lectura devuelve en `warm` las páginas que usó y la clave de `Game.Game`; la siguiente lectura del mismo proceso del juego las pide al principio en unos pocos lotes (se guardan en settings.json, así que también sirve al reabrir la app). Medido contra el juego: refresco de ~16 s a 3–5 s; primera lectura de 16–18 s a 12–16 s.
- 0.8.2: a veces `emulator-5554` no responde a adb (sobre todo justo después de arrancar el servidor) y toda la lectura fallaba a los 15 s con el comando de adb en crudo. `discover()` consulta los dispositivos en paralelo (`probe()`, 5 s como máximo cada uno) y, en cuanto uno responde, los demás tienen 1,5 s más (`PROBE_GRACE`): las copias del mismo emulador y un segundo emulador real responden igual de rápido, una conexión colgada se ignora. Si ninguno responde, o adb se agota a mitad de lectura, sale un mensaje traducido en lugar del comando.
