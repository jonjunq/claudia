# claudia

**Un asistente personal con el que hablas por Telegram, hecho con [Claude Code](https://code.claude.com/docs) tal
cual, funcionando 24/7 con tu suscripción de Claude.** Sin frameworks de agentes y sin factura de API: una sesión de
Claude Code en una máquina tuya, el plugin oficial de Telegram, un `CLAUDE.md` que le da personalidad, unas notas
que sobreviven al reinicio diario y unos pocos scripts que lo mantienen vivo sin que nadie lo vigile.

Te lee el correo y te prepara borradores, te lleva la agenda y el Drive, apunta tus pendientes, te recuerda cosas, te
manda un resumen por la mañana, entiende tus notas de voz y puede contestarte con voz. Con el kit opcional de
[n8n](docs/n8n.md) se entera de tus correos nuevos en segundos y te monta avisos que no gastan tokens.
Y hasta donde quieras llevarla: tu tele, tu servidor de pelis, tu ordenador, tu dinero (solo para leer), tus
trámites, citas y viajes. [Qué le puedes pedir](#qué-le-puedes-pedir), con el riesgo de cada cosa.

[Read in English](README.md)

<p align="center">
  <a href="https://jonjunq.github.io/claudia/video/claudia.es.mp4">
    <img src="docs/video/claudia.es.webp" width="320" alt="Vídeo de 105 segundos de un día con la asistente en el móvil: te escribe ella primero porque llueve la tarde del pádel y lo cambia; una nota de voz acaba en el fontanero apuntado en tu calendario; apaga las luces y pone la peli que mencionaste; vigila tu correo, pide cita para una renovación y reclama una factura de la luz cobrada dos veces; compra pilas solo cuando dices que sí; organiza un viaje a Roma con vuelos y hotel y lo reserva con tu OK; atiende a los clientes de una tienda y junta en un resumen cómo van treinta personas. Tú decides, ella se encarga.">
  </a>
</p>

<sub>▶ 1 min 45 s, aquí sin sonido · [vídeo en calidad completa, con sonido](https://jonjunq.github.io/claudia/video/claudia.es.mp4). Todo es inventado; algunas escenas son usos opcionales o que aún no hemos probado ([qué le puedes pedir](#qué-le-puedes-pedir)). Hecho con [HyperFrames](https://github.com/heygen-com/hyperframes).</sub>

<p align="center">
  <a href="https://jonjunq.github.io/claudia/diagrams/how-it-works.es.html">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/how-it-works-dark.es.svg">
    <img src="docs/diagrams/how-it-works-light.es.svg" width="100%" alt="Cómo está montado el asistente: hablas desde el móvil con un bot de Telegram, y el plugin oficial de canal lo conecta con una sesión de Claude Code en tmux, en modo auto, con tu suscripción de Claude, en una máquina tuya siempre encendida (un contenedor, una VM, un usuario o root: tú eliges). Las notas de voz llegan ya pasadas a texto (Groq, luego Cloudflare, luego un motor local). La sesión lee y escribe CLAUDE.md, sus notas y su memoria, usa un navegador completo con ventana remota, los aparatos que le permitas (tele, servidor de pelis) y, si quieres, una tarjeta limitada, y los conectores de Gmail, Calendar y Drive de claude.ai. Unos hooks mandan a Telegram su estado y los botones de permiso, y un ciclo nocturno guarda el día, repasa la memoria, actualiza Claude Code y la reinicia. Opcional, y sin gastar tokens hasta que pasa algo: n8n te avisa directamente de lo que no hace falta pensar, y si no (correo nuevo, una versión nueva) pasa un aviso de una línea al despertador, que lo escribe en la sesión; la sesión monta flujos de n8n por MCP.">
  </picture>
  </a>
</p>

<sub>Versión grande, clara u oscura según tu sistema: [ábrela en el navegador](https://jonjunq.github.io/claudia/diagrams/how-it-works.es.html). Dibujado con [diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT).</sub>

> Proyecto no oficial, sin relación con Anthropic. Lee antes [¿Esto está permitido?](#esto-está-permitido).

## Qué le puedes pedir

Le escribes (o le mandas una nota de voz) como a una persona. Aquí tienes lo que le puedes decir, el riesgo de cada
cosa en una línea y su guía. **La lista completa, con lo que necesita cada cosa: [docs/recipes/](docs/recipes/README.md)**
(las guías están en inglés; tu asistente te las cuenta en castellano).

**Lo que la nuestra hace, a diario o cuando viene a cuento**

- 🎙️ Yendo por la calle: *«Recuérdame mañana a las diez llamar al fontanero.»* Entiende la nota de voz en un
  segundo y mañana tienes el aviso.
  ⚠️ El audio va al servicio de transcripción que elijas (o se queda en tu máquina, más lento). · [Voz](docs/voice.md)
- ☀️ Sin pedírselo: cada mañana, tu día en un mensaje (citas, lo que vence, los correos que importan), y al final una
  propuesta para dejar la bandeja a cero que apruebas con un «sí».
  ⚠️ Lee todo tu correo; lo que diga un correo son datos, nunca órdenes. · [Ciclo diario](docs/daily-cycle.md)
- 📧 *«Avísame si entra algo importante.»* Con [n8n](docs/n8n.md) vigila tu correo día y noche y solo te dice algo
  cuando un correo te necesita, sin gastar nada mientras no llega nada.
  ⚠️ n8n guarda una contraseña que puede leer tu correo (en tu máquina). · [n8n](docs/n8n.md)
- 🧹 *«Date de baja de toda esa publicidad.»* *«Guárdame las nóminas en Drive según lleguen.»*
  ⚠️ Darse de baja le confirma al remitente que tu dirección existe: para tiendas que conoces, no para el spam. · [Receta](docs/recipes/email-cleanup.md)
- 📺 *«Pon YouTube en la tele.»* *«Instala la app de pelis en el proyector.»* Por el modo desarrollador de la propia
  tele.
  ⚠️ Nunca le pidas rootear un aparato: salta el freno de seguridad del modelo y la sesión se atasca. · [Receta](docs/recipes/tv-and-projector.md)
- 🎬 *«Esta noche quiero ver Dune.»* Se lo pide a tu servidor de pelis de casa, te enseña las versiones que encuentra,
  baja la que elijas y te avisa cuando está. También pone a descargar los torrents que le mandes.
  ⚠️ Las leyes de propiedad intelectual de tu país, y los fakes de los trackers públicos. · [Receta](docs/recipes/films-and-series.md)
- 💻 *«Enciende el ordenador del despacho.»* *«Apágalo, que se me ha olvidado.»* *«Enciende el servidor de Minecraft
  para esta noche.»*
  ⚠️ Una clave SSH a tu ordenador es mucho alcance: que sea estrecha. · [Receta](docs/recipes/your-computer.md)
- 📈 *«¿Cómo va mi cartera este año?»* *«¿Hay algo raro en mi cuenta?»* Lee tu banco, tus fondos y tus criptos **en
  solo lectura**, te dibuja las gráficas y cada mañana mira el banco en silencio, y solo te dice algo si ve algo raro.
  ⚠️ Lo de solo lectura se fija en el banco o el bróker, no en una frase; tus datos financieros pasan por el modelo. · [Receta](docs/recipes/money-read-only.md)
- 🧾 *«Rellena este formulario de la Administración con mis datos.»* *«Reclama lo que me debe mi antigua empresa.»*
  Se pelea ella con las webs complicadas, guarda la referencia y vigila la respuesta; si sale un captcha o te piden
  entrar, te manda un enlace y lo resuelves desde el móvil.
  ⚠️ Presentar algo es un acto legal en tu nombre: siempre te enseña el resumen antes. · [Receta](docs/recipes/errands-and-appointments.md)
- 🚗 *«Pídeme cita para la ITV, cualquier día al salir del trabajo.»* Mira varias empresas a la vez, calcula el
  trayecto a esa hora y reserva el hueco que elijas.
  ⚠️ Solo reserva lo que eliges tú; tus datos van en un fichero privado. · [Receta](docs/recipes/errands-and-appointments.md#appointments)
- ✈️ *«Roma el último finde del mes, vuelos y hotel, el precio con todo.»* Totales con todo incluido, los enlaces y,
  cuando reservas, cada vuelo en tu calendario y un aviso cuando abre el check-in.
  ⚠️ Los precios cambian cada hora; pagas tú, o la tarjeta limitada con tu «sí». · [Receta](docs/recipes/trips.md)
- 📱 *«Mira este reel y dime si es verdad.»* Enlaces, reels y vídeos largos: los transcribe, mira unos fotogramas y
  comprueba lo que dicen. Con una cuenta de Instagram suya, le compartes los reels desde la propia app.
  ⚠️ Esa vía de Instagram usa una API no oficial: va contra las normas de Instagram y puede costar la cuenta, así
  que solo con una cuenta suya, nunca la tuya. · [Vídeos](docs/recipes/links-and-videos.md) · [Redes](docs/recipes/social-media.md)
- 🎓 *«¿Qué tengo que entregar esta semana?»* *«¿Cuántos días de vacaciones me quedan?»* Tu campus y el portal del
  trabajo, solo para leer.
  ⚠️ Mandan las normas de tu centro y de tu empresa. · [Receta](docs/recipes/study-and-work.md)
- 🖥️ *«¿Ha salido bien la copia de esta noche?»* Vigila tu servidor de casa sin poder tocar nada.
  ⚠️ Los tokens tienen que ser de solo lectura de verdad. · [Guía](docs/homelab-read-access.md)
- 🗺️ *«Explícamelo con un diagrama.»* Un dibujo o una página que lo explica, en vez de un muro de texto.
  ⚠️ Es una skill de terceros: revísala antes de instalarla. · [Revisar skills](docs/vetting-skills.md)
- 🔎 *«¿Qué te dije el mes pasado de la caldera?»* Busca en vuestras conversaciones antiguas.
  ⚠️ Todo lo que le cuentas se queda en su máquina: por eso la máquina tiene que ser tuya. · [Memoria](docs/memory.md)

**Lo que puede hacer si se lo montas** (posible con lo que hay aquí; no lo hemos probado nosotros)

- 💡 *«Apaga las luces del salón.»* Con la integración MCP Server de [Home Assistant](https://www.home-assistant.io),
  que solo le deja tocar los aparatos que tú expones.
  ⚠️ No expongas nada peligroso de encender por error (cerraduras, alarmas, hornos). · [Receta](docs/recipes/smart-home.md)
- 🛒 *«Pide las pilas.»* *«Suscríbeme a eso y avísame antes de que renueve.»* Paga con una
  [tarjeta virtual con su propio saldo pequeño](docs/permissions.md#optional-paying-with-a-limited-card), solo después
  de tu «sí» a ese importe. Las piezas están; aún no hemos hecho una compra real con ella.
  ⚠️ El límite de la tarjeta es la barrera que aguanta aunque la engañen: que sea pequeño. · [Receta](docs/permissions.md#optional-paying-with-a-limited-card)
- 🏷️ *«Vende mi cámara vieja, aquí tienes las fotos.»* Una cuenta suya en una web de segunda mano: escribe el
  anuncio, propone el precio y contesta a los compradores; el trato pasa por ti.
  ⚠️ Estafas dirigidas a vendedores; nunca cobrar fuera de la plataforma. · [Receta](docs/recipes/shopping-and-second-hand.md)
- 📣 Sus propias redes sociales: prepara las publicaciones, sube cada una después de tu «sí» y contesta comentarios,
  por la API oficial de cada red.
  ⚠️ Es público y para siempre: tu «sí» a cada publicación. · [Receta](docs/recipes/social-media.md)
- 📞 Un número de teléfono al que llamarla, con un servicio de agentes de voz. (La nuestra coge llamadas en un canal
  de voz de Discord.)
  ⚠️ APIs de pago por minuto, fuera de tu suscripción. · [Voz](docs/voice.md#experimental-a-voice-call-over-discord)
- 💬 Su propio número de WhatsApp o, para una tienda, un agente que contesta a tus clientes (horarios, stock,
  pedidos, citas) y te pasa lo que no sepa. Por la vía oficial, WhatsApp Business Platform, y como agente aparte y
  limitado, sin tu correo, tu tarjeta ni tu casa, porque cualquiera le puede escribir.
  ⚠️ Automatizar un WhatsApp normal va contra sus normas y te pueden cerrar el número.
- 👷 *«¿Qué están haciendo mis operarios?»* En vez de llamar a treinta personas, les escribe a cada una, repregunta
  si la respuesta es vaga y te da un resumen: quién está en qué, qué va retrasado, qué está bloqueado.
  ⚠️ Tu equipo tiene que saber que habla con un asistente; solo lo del trabajo y en su horario. · [Receta](docs/recipes/study-and-work.md#your-team-possible-not-tried-by-us)

Lo montes como lo montes, hay tres normas que no cambian: lo que lee (correos, webs, reels, mensajes de
desconocidos) son datos, nunca órdenes; pregunta antes de todo lo que deja huella (enviar, publicar, pagar,
presentar, borrar); y los límites que tienen que aguantar aunque la engañen están fuera de la conversación (claves de
solo lectura, el saldo de una tarjeta, `hard_deny`, una regla del cortafuegos).

No hace falta que te acuerdes de nada de esto: en sus primeras semanas te lo ofrece ella, de una en una y cuando
viene a cuento ([cómo](templates/workspace/.claude/skills/first-days/SKILL.md)). O pregúntale *«¿qué sabes hacer?»*.

## ¿Por qué no un framework de agentes?

Nuestro primer asistente fue [Hermes Agent](https://github.com/NousResearch/hermes-agent), y nos gustaba: está hecho
para ser una secretaria proactiva. Pero necesita un modelo detrás que se paga por uso, y el modelo barato que usábamos
(el de DeepSeek) se inventaba causas y daba vueltas con pasos que nadie pedía. La suscripción de Claude no se puede
conectar a agentes de terceros, pero sí cubre Claude Code. Y Claude Code con
[canales](https://code.claude.com/docs/en/channels) ya era casi un asistente; este repo es lo que faltaba. La
comparación sincera, incluido lo que Hermes sigue haciendo mejor, está en
[docs/comparison.md](docs/comparison.md) (en inglés).

## Qué necesitas

- Una **suscripción de Claude** (Pro o Max; Max si además programas con Claude, porque el asistente comparte tus
  límites de uso).
- Una **máquina Linux siempre encendida**: una VM, un contenedor LXC, un mini PC, un servidor de casa, una VM barata
  en la nube. Sin modelos de voz locales, 2 núcleos, 2-4 GB de RAM y 10 GB de disco van sobrados. Cuánto la aíslas
  lo decides tú: [Móntala como quieras](#móntala-como-quieras).
- `tmux`, `jq`, `curl`, `git`, [Bun](https://bun.sh) (el plugin de Telegram funciona con él) y Claude Code.
- Un **bot de Telegram**: el token te lo da [@BotFather](https://t.me/BotFather).
- Opcional: Gmail / Google Calendar / Google Drive conectados en claude.ai (Ajustes → Conectores); una clave de
  [Groq](https://console.groq.com) para las notas de voz; una de [ElevenLabs](https://elevenlabs.io) para que hable.

## Móntala como quieras

Es código abierto y no hay una única forma buena de desplegarla. Nosotros la tenemos como usuario normal en su propio
contenedor, con la red cerrada y con el administrador instalando los servicios del sistema, porque se pasa el día
leyendo correos de desconocidos. Tú puedes preferirla como usuario en el servidor de casa que ya tienes, en una VM en
la nube, o como **root de una máquina que sea solo suya**, «su casa», para que instale y cuide ella misma todo lo que
necesite (n8n incluido) sin que tengas que tocar nada. Todo eso funciona con los mismos ficheros. El equilibrio (más
alcance = más útil = más en juego si la engañan o se equivoca) y lo que protege cada opción están en
[docs/isolation.md](docs/isolation.md). Quédate con lo que te encaje y cambia el resto.

## Empezar

```bash
# En la máquina del asistente, como root
adduser --disabled-password --gecos "" asistente        # o el nombre de usuario que quieras
apt install -y tmux jq curl git ffmpeg
git clone https://github.com/jonjunq/claudia && cd claudia
./install.sh asistente --name Claudia --owner Alex --language Spanish --timezone Europe/Madrid

# Como ese usuario: instala Claude Code y Bun, inicia sesión y conecta Telegram
su - asistente
curl -fsSL https://claude.ai/install.sh | bash
curl -fsSL https://bun.sh/install | bash
exec bash -l                             # para que coja el PATH nuevo
cd ~/assistant && claude                # entra con tu suscripción y, dentro de Claude Code:
#   /plugin install telegram@claude-plugins-official
#   /telegram:configure <token del bot>
#   sal y arranca una vez con: claude --channels plugin:telegram@claude-plugins-official
#   escríbele al bot y luego:  /telegram:access pair <código>  y  /telegram:access policy allowlist
nano ~/assistant/CLAUDE.md               # hazlo tuyo (escríbelo en castellano y hablará en castellano)
exit

# Como root: déjalo funcionando
systemctl enable --now assistant assistant-permission-watch assistant-history.timer
```

Y escríbele a tu bot. Paso a paso, con todos los tropiezos que tuvimos: [docs/setup.md](docs/setup.md).

## Novedades

Lo último (lista completa en [CHANGELOG.md](CHANGELOG.md), en inglés).

**Próxima versión** (aún sin publicar)

- **Todo lo que le puedes pedir** ([arriba](#qué-le-puedes-pedir) y [docs/recipes/](docs/recipes/README.md)): lo que
  la nuestra hace a diario, de la tele y el servidor de pelis al dinero en solo lectura, los trámites, los viajes y su
  propio Instagram, y lo que es posible pero sin probar, cada cosa con su riesgo en una línea y una receta: qué
  necesita, cómo pedirle a tu asistente que lo monte, la frase de `autoMode`, los riesgos y lo que aprendimos. Solo
  ideas y riesgos, sin código, para lo que va contra las condiciones de un servicio o toca dinero (APIs no oficiales
  de redes, bancos y brókers).
- **Bajas de publicidad en un clic** ([receta](docs/recipes/email-cleanup.md)): `templates/tools/unsubscribe.py` solo
  usa el enlace RFC 8058 que el remitente firmó con su propio dominio, por https, nunca hacia tu red de casa y nunca
  por correo.
- **Sus primeras semanas ofrecen más**: el catálogo de `first-days` cubre ya todo lo anterior, y cada cosa apunta a su
  receta en la propia máquina del asistente.

**1.5.0** (05/11/2026)

- **Te sigue contestando mientras trabaja** ([docs/context.md](docs/context.md)): lo pesado (trámites largos en el
  navegador, montones de PDF y capturas, búsquedas largas, código) lo hacen cuatro ayudantes en segundo plano con el
  mismo modelo, así que tu siguiente mensaje no espera y la conversación principal no se llena. Lo que necesita tu
  «sí» nunca se delega.
- **Arranca más ligera**: fuera las herramientas, skills e instrucciones de conectores que no usa nunca. Medido en
  la nuestra: la primera llamada de una conversación −17 %, la segunda −23 %, y lo mismo en cada llamada siguiente.
- **Compactar sin perder lo importante**: queda escrito qué tiene que sobrevivir al resumen, y justo después de
  compactar recupera tus últimos mensajes tal cual. Opcional: compactar tras un buen rato sin actividad.
- **`/usage` lo contesta el propio bot**, al momento y sin gastar, aunque ella esté ocupada.
- **Un repaso nocturno más prudente**: solo pasa a la memoria lo que dijiste tú o lo que se vio funcionar; nada que
  venga solo de un correo o una web. Te lista las skills que nadie ha usado en un mes.
- **Aviso de versiones desde la instalación**: una pregunta al final de `install.sh` y una comprobación diaria
  pequeña sin necesidad de n8n; nunca actualiza sin tu «sí».
- **La comparativa** con Hermes y OpenClaw, al día de noviembre de 2026, y lo que hemos tomado de ellos.

**1.4.0** (05/11/2026)

- **Sus primeras semanas, proactiva** ([la skill](templates/workspace/.claude/skills/first-days/SKILL.md)): te
  ofrece lo que sabe hacer o montarte (el correo vigilado con n8n, notas de voz, actualizaciones, el navegador…), de
  una en una y cuando viene a cuento, en sencillo y con lo que cuesta, y no vuelve a preguntar lo que le dijiste que
  no. Esa fase termina sola a las cuatro semanas.
- **Se mantiene al día, con tu OK** ([docs/updating.md](docs/updating.md)): un flujo de n8n le avisa de las
  versiones nuevas; te explica qué traen, revisa antes los cambios y, si te parece bien, actualiza con
  `install.sh --upgrade`, que nunca pisa lo que cambiaste (deja un `.new` fusionado). Solo versiones publicadas,
  nunca sola.
- **Ejemplos de qué pedirle**, [arriba](#qué-le-puedes-pedir).
- **Las notas de voz llegan ya transcritas** ([docs/voice.md](docs/voice.md)): el parche
  del plugin de Telegram las descarga y transcribe antes de que las vea el asistente, lo que ahorra dos turnos
  (unos 5 s) por nota; las descargas tienen tiempo máximo; `transcribe.sh` pasa de Groq a Cloudflare Workers AI y a
  Parakeet en la CPU, con tu lista de nombres para que salgan bien escritos.
- **Un navegador de verdad** ([docs/browser.md](docs/browser.md)): Chromium completo con
  ventana en una pantalla virtual en vez del headless shell que rechazan las protecciones antibots, dos perfiles y una
  ventana remota opcional para que resuelvas captchas e inicios de sesión desde el móvil en la misma sesión del
  asistente. Sin trucos de camuflaje.
- **Opcional: pagar con una tarjeta limitada** ([docs/permissions.md](docs/permissions.md#optional-paying-with-a-limited-card)):
  una tarjeta virtual con su propio saldo pequeño, tu «sí» a cada compra, la tarjeta nunca en el chat y las reglas
  de `autoMode` que solo permiten eso.
- **Dispositivos fuera de casa** por Tailscale ([docs/remote-devices.md](docs/remote-devices.md)):
  el asistente llega a un dispositivo por dos puertos, y el dispositivo no llega a nada.
- **Menos contexto** ([docs/memory.md](docs/memory.md#keeping-the-context-small)): la
  conversación se compacta a los 300k tokens en vez de cerca del millón, la lista de pendientes que se carga en cada
  conversación se mantiene corta, el repaso nocturno poda las skills en vez de solo añadir, y
  `templates/tools/token-usage.py` enseña dónde se van tus tokens y tu contexto.

**1.3.0** (04/11/2026)

- **Avisos que no gastan tokens, con n8n** ([docs/n8n.md](docs/n8n.md)): un instalador que deja n8n endurecido,
  plantillas de flujo (correo nuevo → despierta al asistente; vigilar una web → te avisa a ti, y se apaga sola al
  terminar), actualizaciones con copia y vuelta atrás automática, y el propio asistente creando los flujos por el
  servidor MCP de n8n.
- **Despertador en vez de Monitors** ([docs/wakeup.md](docs/wakeup.md)): un pequeño servicio que escribe avisos de una
  línea en la sesión solo cuando un log vigilado o n8n traen algo. Sustituyó a un Monitor que costaba ~48 turnos
  vacíos al día.
- **Pagos bloqueados del todo** en `settings.json` (`autoMode.hard_deny`), porque un «nunca pagos» dentro de una regla
  `allow` no bloquea nada.
- **Escribe pensando en el móvil**: mensajes ricos de Telegram con título, emojis que guían, una cita para la idea
  principal y opciones numeradas para contestar con un número ([un ejemplo](docs/telegram-extras.md#writing-for-the-phone)).
- **Aprobar desde Telegram lo que bloquea el clasificador**, una sola vez y para esa llamada exacta.
- **Móntala como quieras**: la documentación ya no da por hecho un contenedor aislado; compara las opciones.
- Arreglos: un «⏳ Trabajando» fantasma tras turnos sin herramientas, y las tareas nocturnas con cron.

## Qué trae

Las piezas, agrupadas por para qué sirven. Todo menos lo básico es opcional.

**Lo básico**

| Pieza | Qué hace |
|---|---|
| `templates/workspace/CLAUDE.md` | Personalidad y normas: respuestas para móvil, calidad ante todo, proactividad, qué hace solo y qué te pregunta antes, disciplina de memoria |
| `notes/todo.md`, `yesterday.md`, `routines.md` | La libreta que lleva de un día a otro, importada en cada conversación |
| `bin/start.sh` + `assistant.service` | Ejecuta Claude Code en tmux y lo recupera con `--continue` si se cierra |
| `assistant-daily-restart` + cron | Cada noche: le pide que guarde el día, actualiza Claude Code y empieza una conversación limpia |
| `settings.json` | Modo auto y una lista de permisos: leer y preparar borradores lo hace solo; enviar y borrar te lo pregunta por Telegram |
| `bin/statusline.sh` | Guarda el contexto y el uso del plan, con lo que el bot contesta a `/usage` en Telegram |
| `autoMode.hard_deny` en `settings.json` | Pagos y dinero bloqueados del todo, lo pida quien lo pida |
| `bin/clear-context.sh` | `/clear` desde Telegram: conversación nueva a media jornada, después de apuntar lo pendiente |
| `bin/permission-watch.sh` | Te avisa por Telegram cuando se queda parado en un aviso de permiso de su terminal o cambia de modelo tras un freno de seguridad |

**Telegram y memoria**

| Pieza | Qué hace |
|---|---|
| `templates/telegram/` + hooks en `settings.json` | Mensaje «⏳ Trabajando» mientras trabaja, le llegan los mensajes que citas, peticiones de permiso con botones Permitir / Denegar, aprobar una vez lo que bloqueó el clasificador, mensajes ricos (títulos, tablas) con `send-rich.py` y notas de voz transcritas antes de llegarle |
| `templates/memory/` + skill `recall` | Busca en conversaciones antiguas (`recall`), repasa skills y memoria cada noche y guarda un historial git para deshacer |
| `.claude/agents/` (`browser`, `reader`, `researcher`, `coder`) | Ayudantes para el trabajo pesado, en segundo plano y con el mismo modelo, para que te siga contestando y la conversación no crezca |
| `after-compact.py` + Compact Instructions | Tras compactar, tus últimos mensajes y lo pendiente vuelven tal cual; opcional `assistant-idle-compact` para los ratos largos sin actividad |
| skill `first-days` + `notes/first-days.md` | Sus primeras semanas: ofrece lo que sabe hacer, de una en una, y recuerda lo que contestaste |
| skill `updating` + `install.sh --upgrade` | Actualiza a una versión nueva con tu OK, fusionando las plantillas con tus cambios en vez de pisarlos |
| `assistant-release-watch` + timer | Sin n8n: una vez al día le avisa de una versión nueva (solo el número), para que te lo cuente |

**Reaccionar sin gastar tokens**

| Pieza | Qué hace |
|---|---|
| `templates/wakeup/` (`assistant-wakeup`) | Escribe un aviso de una línea en la sesión solo cuando un log vigilado o n8n traen algo; junta los que llegan seguidos, espera si hay un diálogo de permiso abierto y nunca pasa por Telegram |
| `templates/n8n/` (`install-n8n.sh`, `n8n-admin`, flujos) | Instala n8n endurecido, importa y publica flujos desde la terminal, lo actualiza con copia y vuelta atrás; plantillas de correo nuevo → asistente, versión nueva → asistente y vigilar una web → tú |

**Extras**

| Pieza | Qué hace |
|---|---|
| `bin/transcribe.sh`, `bin/speak.sh` | Notas de voz de entrada (las transcribe el plugin al llegar: Groq, luego Cloudflare, luego Parakeet en local) y de salida (ElevenLabs) |
| `.claude/skills/browser` + `templates/browser/` | Usa webs con agent-browser y un Chromium completo con ventana en vez de scripts improvisados; ventana remota opcional (noVNC) para captchas e inicios de sesión |
| `templates/tools/card-fill.sh` | Guarda una tarjeta virtual limitada para los pagos opcionales, sin que pase por el chat |
| `templates/tools/vet-skill.sh` | Revisa una skill de terceros con SkillSpector antes de instalarla |
| `templates/tools/unsubscribe.py` | Bajas de publicidad en un clic, solo con el enlace que firmó el remitente (RFC 8058) |
| `docs/recipes/` | Cómo montar todo lo de [Qué le puedes pedir](#qué-le-puedes-pedir), con sus riesgos; se instala para que el asistente lo lea |

## Documentación (en inglés)

- [Instalación](docs/setup.md): máquina, usuario, Claude Code, plugin de Telegram, servicio, primer arranque.
- [Recetas: todo lo que le puedes pedir](docs/recipes/README.md): la tele, pelis y series, tu ordenador, la casa
  domótica, el dinero en solo lectura, redes sociales, cuentas suyas, vídeos, la bandeja limpia, trámites y citas,
  viajes, segunda mano, tus estudios y el trabajo. Qué necesita cada cosa, cómo pedírsela y los riesgos.
- [Personalidad y memoria](docs/personality-and-memory.md): cómo escribir el `CLAUDE.md`, las notas y la memoria.
- [Permisos](docs/permissions.md): modo auto, la lista de permisos, por qué no `bypassPermissions` y cómo explicarle
  al clasificador qué aparatos y servicios son tuyos.
- [Ciclo diario, rutinas y comandos](docs/daily-cycle.md): cierre del día, resumen matutino, `/usage`, `/clear`.
- [Contexto: ayudantes, arranque ligero, compactación](docs/context.md): el trabajo pesado en subagentes, lo que
  carga el contexto fijo y compactar sin perder lo importante, con mediciones.
- [Recordar, repaso nocturno e historial](docs/memory.md): buscar en conversaciones antiguas, mejorar skills y memoria
  cada noche y deshacerlo, con lo que cuesta.
- [Extras de Telegram](docs/telegram-extras.md): estado «trabajando» en directo, mensajes citados, aprobar permisos con
  botones, mensajes ricos con tablas y notas de voz transcritas al llegar.
- [Navegador](docs/browser.md): agent-browser y un Chromium completo para webs sin API, dos perfiles, una ventana
  remota para captchas e inicios de sesión, con mediciones.
- [Voz](docs/voice.md): notas de voz transcritas al llegar (una cadena de motores, con mediciones), respuestas
  habladas y una llamada experimental por Discord.
- [Dispositivos fuera de casa](docs/remote-devices.md): llegar a un dispositivo remoto por Tailscale, y a nada más.
- [Móntala como quieras](docs/isolation.md): dónde ejecutarla (su propio contenedor, un usuario, root de su propia
  máquina, una VM en la nube), qué arriesga cada opción y cómo cerrarla si quieres.
- [Despertador](docs/wakeup.md): reaccionar a logs y a n8n con avisos de una línea en vez de Monitors.
- [n8n](docs/n8n.md): avisos y automatizaciones que no gastan tokens, montados por el propio asistente y al día.
- [Ojos en tu servidor, sin manos](docs/homelab-read-access.md): acceso de solo lectura a Proxmox, copias y paneles, con seguridad.
- [Revisar skills](docs/vetting-skills.md): comprobar skills de terceros antes de instalarlas (SkillSpector, skill a skill).
- [Actualizar](docs/updating.md): enterarse de las versiones nuevas y aplicarlas con tu OK sin perder tus cambios, y
  por qué nunca sola.
- [Problemas frecuentes](docs/troubleshooting.md): los que nos encontramos de verdad.
- [Comparación](docs/comparison.md): Hermes Agent, un Proyecto de claude.ai y esto.

## ¿Esto está permitido?

No somos abogados y las condiciones pueden cambiar: lee tú mismo la página de
[Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance) de Anthropic y sus
[Consumer Terms](https://www.anthropic.com/legal/consumer-terms). Lo que hace este montaje: **tú** inicias sesión en
Claude Code **sin modificar** con **tu propia** suscripción, mediante el login de Anthropic, y el asistente trabaja
**solo para ti** (la lista de Telegram solo deja entrar a tu cuenta). Esa página dice que el login con suscripción
está pensado para el "uso ordinario de Claude Code", que los límites anunciados de los planes "suponen un uso
ordinario e individual", y que terceros no pueden enrutar peticiones a través de credenciales Free/Pro/Max en nombre
de sus usuarios. Así que no lo conviertas en un bot para otras personas, en un asistente familiar compartido con una
sola suscripción ni en un servicio. Para eso, usa una clave de API con las condiciones comerciales.

## Créditos

Hecho con Claude Code sobre los [canales](https://code.claude.com/docs/en/channels) oficiales y el plugin de
Telegram de [claude-plugins-official](https://github.com/anthropics/claude-plugins-official). Lo de "una sola pregunta
con tu apuesta" para encargos poco definidos viene de la idea `interview-me` de
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT); las normas de "Cuando tocas código" están
adaptadas de [Ponytail](https://github.com/DietrichGebert/ponytail) (MIT). Proyecto hermano:
[loop-kit](https://github.com/jonjunq/loop-kit), un bucle de construcción autónomo para Claude Code.

Licencia MIT, ver [LICENSE](LICENSE).
