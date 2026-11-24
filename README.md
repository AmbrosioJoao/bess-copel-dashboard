# BESS Rural — painel SCADA simplificado

Site estático publicado com GitHub Pages. Mostra um SEP rural de 13,8 kV, uma falha clicável no alimentador e dois indicadores: tensão da bateria e economia estimada em reais.

## Conteúdo

- `index.html` — página e diagrama unifilar em SVG.
- `styles.css` — tema cinza com detalhes em laranja COPEL.
- `app.js` — interação do ponto de falha e alternância do estado.
- `assets/` — logos UTFPR e COPEL.
- `prints/` — registros de telas do projeto anterior.
- Documentos locais: `problema-copel.md` e a entrevista em PDF, preservados e fora do versionamento conforme `.gitignore`.

## Executar localmente

```bash
python3 -m http.server 8000
```

Acesse `http://localhost:8000`.

## Publicação

O site é servido diretamente da branch `main` pelo GitHub Pages.
