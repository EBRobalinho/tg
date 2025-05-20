
# STCAD – Structural Connections for AutoCAD

Aplicativo desktop desenvolvido em Python para o **dimensionamento e detalhamento automático de ligações metálicas estruturais**, com integração ao **AutoCAD** para geração de desenhos técnicos em formato `.dwg`.

---

## 🎯 Objetivo

O STCAD tem como propósito **auxiliar engenheiros civis e estruturais** no cálculo e modelagem de conexões entre vigas e pilares metálicos, automatizando tarefas repetitivas e reduzindo erros no processo de detalhamento.

---

## ⚙️ Funcionalidades

- Seleção de tipos de ligação com visualização por ícones;
- Cálculo automático das dimensões das peças com base nos dados inseridos;
- Geração direta dos elementos no AutoCAD via interface COM;
- Interface gráfica com **PySide6 (Qt for Python)**;
- Exportação de parâmetros dimensionais;
- Acesso integrado a manuais, normas e documentos de apoio em PDF;
- Janela "Sobre" e "Ajuda" com informações úteis;
- Estilo visual adaptável, com barra de título customizada e responsiva.

---

## 📐 Tipos de ligações disponíveis

- ✅ Viga sobre Pilar (Rígida)
- ✅ Chapa de Cabeça (Rígida)
- ✅ Chapa de Extremidade (Flexível)
- ✅ Cantoneira Flexível – Parafusada
- ✅ Cantoneira Flexível – Soldada

---

## 🛠️ Tecnologias utilizadas

- [Python 3.11+](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython/)
- [pyautocad](https://pypi.org/project/pyautocad/)
- `win32com.client` (automação COM)
- AutoCAD 2023 ou superior
- Estrutura modular com separação por tipos de ligação

---

## ▶️ Como executar

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/stcad.git
   cd stcad
   ```

2. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Execute o aplicativo:
   ```bash
   python interface_ligacoes_final.py
   ```

⚠️ O AutoCAD deve estar instalado no computador e licenciado corretamente.

---

## 📂 Estrutura do Projeto

```
python_app/
├── front/
│   ├── janela_principal.py
│   ├── base_form.py
│   ├── barra_superior.py
│   └── ... (parâmetros de cada ligação)
├── v_p_viga_sobre_pilar/
├── v_p_chapa_cabeca/
├── documentos/
│   ├── manual_usuario.pdf
│   ├── exemplos_uso.pdf
│   └── normas_tecnicas.pdf
├── imagem_logo/
│   ├── cepe_logo.png
│   └── fab_logo.png
└── interface_ligacoes_final.py
```

---

## ✍️ Autor

Aplicativo desenvolvido por **Aspirante a Oficial Engenheiro Robalinho**  
Projeto de graduação em Engenharia Civil – ITA  
Para uso interno no **Centro de Estudos e Projetos de Engenharia (CEPE)** da Força Aérea Brasileira (FAB).

---

## 📜 Licença

Uso restrito ao ambiente institucional da FAB.  
Distribuição externa ou comercialização não autorizada.
