"""Chapter 12 – Anexo (client PDF 'CAPITULO_IDENTIDAD_METODO_ULA_BARRE'), defined by hand."""

def steps(items):
    return '<div class="steps">' + ''.join(
        f'<div class="step"><span class="n">{n}</span><div><h3>{t}</h3>{"".join(f"<p>{p}</p>" for p in ps)}</div></div>'
        for n, t, ps in items) + '</div>'

def annex_pages(figure_row, quote_html):
    CH, NAME = '12', 'Anexo: identidad del método'
    P = []
    def add(title, kicker, custom):
        P.append({'n': 200 + len(P), 'chap': CH, 'chapname': NAME, 'title': title, 'kicker': kicker, 'blocks': [], 'custom': custom})

    add('Identidad del método', 'Identidad, estructura y estandarización', (
        ['<p class="lead">Capítulo complementario para el Manual Oficial de Formación. Su finalidad es definir los elementos comunes que deben conservarse en todas las sesiones, independientemente de la persona que las imparta.</p>'],
        [figure_row([{'img': 'image127.jpg'}])],
        [steps([('01', 'Identidad del método', ['ULA Barre combina fuerza, resistencia, control postural, movilidad y musicalidad mediante una programación planificada. Su identidad reside tanto en la selección de movimientos como en el orden de los bloques, la sincronización musical, la progresión mensual y la adaptación individual.'])])],
        [], 'ex'))

    weeks = [('Base técnica', 'Sesión original: familiarización, alineación, control y aprendizaje de secuencias.'),
             ('Resistencia', 'Incorporación de muñequeras lastradas a lo largo de la sesión, cuando sean adecuadas para cada participante.'),
             ('Mayor estímulo', 'Aumento planificado de la utilización e intensidad de los props en más canciones.'),
             ('Integración', 'Combinación de muñequeras, mayor intensidad de props y mancuernas de más peso cuando la técnica lo permita.')]
    wk = ''.join(f'<div class="week w{k + 1}"><span class="wl">Semana {k + 1}</span><h3>{t}</h3><p>{d}</p><span class="wbar"><i style="width:{25 * (k + 1)}%"></i></span></div>' for k, (t, d) in enumerate(weeks))
    add('Programación y progresión de cuatro semanas', None, (
        ['<p class="lead">La programación mensual avanza en cuatro etapas, de la base técnica a la integración de todos los recursos.</p>'] if False else [],
        [f'<div class="weeks">{wk}</div>'],
        [],
        ['<div class="hl"><span class="bar"></span><p>La sesión mantiene una base reconocible durante el mes: se progresa sin sacrificar la calidad del movimiento.</p></div>'], 'late'))

    blocks = [('Calentamiento global y técnico', 5), ('Tren inferior en barra', 15), ('Tren superior con mancuernas', 10),
              ('Glúteos en suelo', 5), ('Abdomen: crunch y planchas', 8), ('Estiramientos y vuelta a la calma', 7)]
    tl = ''.join(f'<div class="tl"><span class="n">{k + 1:02d}</span><span class="nm">{b}</span><span class="bar"><i style="width:{m / 15 * 100:.0f}%"></i></span><span class="tm">{m} min</span></div>' for k, (b, m) in enumerate(blocks))
    tl += '<div class="tl total"><span class="n"></span><span class="nm">Total</span><span class="bar"></span><span class="tm">50 min</span></div>'
    add('Estructura de una sesión de 50 minutos', None, (
        ['<p class="lead">La siguiente distribución es una propuesta de ajuste para conciliar los seis bloques descritos con la duración oficial de 50 minutos.</p>'],
        [f'<div class="timeline">{tl}</div>'],
        [],
        ['<div class="note"><div class="k">Importante</div><p>Debe validarse con la programación musical antes de fijarla como guion definitivo.</p></div>'], 'late'))

    add('Música, orden y danza clásica', None, (
        [],
        [steps([
            ('04', 'Música como eje de la clase', ['Cada canción determina secuencias, repeticiones, cambios de lado, pausas, explicaciones y transiciones. La instructora anticipa las indicaciones para mantener el flujo, sin detener la música innecesariamente. La intensidad debe surgir de una programación coherente, no de interrupciones improvisadas.']),
            ('05', 'Orden, material y armonía del estudio', ['Los props se introducen y retiran según la secuencia planificada. El orden reduce interrupciones y conserva una disposición visual limpia. La esterilla se incorpora al llegar al trabajo en suelo, evitando que obstaculice el resto de la sesión.']),
            ('06', 'Recursos de danza clásica', ['Se utilizan posiciones, alineación, apertura de cadera dentro del rango individual, extensiones de piernas y coordinación inspiradas en danza clásica. El objetivo no es enseñar ballet profesional, sino aprovechar sus recursos para desarrollar postura, movilidad, control y calidad del movimiento.'])])],
        [], [], 'late'))

    add('Adaptación y estandarización', None, (
        [],
        [steps([
            ('07', 'Adaptación sin perder la estructura', ['Todas las personas siguen el mismo recorrido de bloques, con alternativas de rango, apoyo, resistencia, posición o ejercicio. Ante diástasis abdominal u otra condición que precise ajustes, se ofrecen variantes de core apropiadas y se respetan las indicaciones clínicas individualizadas; no existe una única modificación válida para todos los casos.']),
            ('08', 'Estandarización: una experiencia ULA', ['La programación oficial define orden de bloques, playlist, secuencias, cambios, props y progresiones. Todas las personas instructoras deben respetar estos elementos para que la experiencia prometida sea consistente, con independencia de quién dirija la sesión.',
                                                         'La adaptación individual no equivale a modificar la programación general. Las variaciones necesarias se aplican a la persona, preservando el diseño de la clase. Cualquier cambio estructural o incorporación de material no previsto debe acordarse previamente con la persona responsable de la programación.'])])],
        [], [], 'late'))

    crit = [('Antes de cada clase', 'Revisar programación, playlist, material y alternativas.'),
            ('Durante la clase', 'Seguir el guion musical, anticipar transiciones, observar técnica y ofrecer opciones sin detener el grupo.'),
            ('Después', 'Registrar incidencias y propuestas de mejora para su revisión coordinada.')]
    cards = ''.join(f'<div class="card"><span class="n">{k + 1:02d}</span><h3>{t}</h3><p>{d}</p></div>' for k, (t, d) in enumerate(crit))
    add('Criterios de impartición', None, (
        ['<p class="lead">Tres momentos, un mismo estándar: así se garantiza la experiencia ULA en cada sesión.</p>'] if False else [],
        [f'<div class="k-label">09 · Criterios de impartición</div><div class="cards c3 crit">{cards}</div>'],
        [],
        ['<div class="motto"><span>Misma esencia</span><i></i><span>Misma estructura</span><i></i><span>Misma experiencia</span></div>'], 'late'))
    return P
