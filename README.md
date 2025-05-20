
# STCAD – Structural Connections for AutoCAD

Aplicativo desktop desenvolvido em Python para o **dimensionamento e detalhamento de ligações metálicas estruturais**, com integração ao **AutoCAD** para geração de desenhos técnicos em formato `.dwg`.

---

## 🎯 Objetivo

O STCAD tem como propósito **auxiliar engenheiros** no cálculo e modelagem de conexões entre vigas e pilares metálicos, automatizando tarefas repetitivas e reduzindo erros no processo de detalhamento.

---

## ⚙️ Funcionalidades

- Seleção de tipos de ligação com visualização por ícones;
- Cálculo automático das dimensões das conexões com base nos dados inseridos;
- Geração direta dos elementos no AutoCAD via interface COM;
- Interface gráfica com **PySide6 (Qt for Python)**;
- Exportação de parâmetros dimensionais para arquivo `.txt` ;
- Acesso integrado a manuais de cálculo gratuitos da Gerdau S.A;
- Estilo visual adaptável, com barra de título customizada e responsiva.

---

## 📐 Tipos de ligações disponíveis

- ✅ Viga sobre Pilar (Rígida)
- ✅ Chapa de Cabeça (Rígida)
- ✅ Chapa de Extremidade (Flexível)
- ✅ Cantoneira Flexível – Parafusada
- ✅ Cantoneira Flexível – Soldada
- ✅ Cantoneira Flexível – Parafusada/Soldada

---

## 🛠️ Tecnologias utilizadas

- [Python 3.11+](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython/)
- [pyautocad](https://pypi.org/project/pyautocad/)
- AutoCAD 2023 ou superior
- Estrutura modular com separação por tipos de ligação
- Programação orientada a objetos

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
   python main.py
   ```

⚠️ O AutoCAD deve estar instalado no computador e licenciado corretamente.

---

## 📂 Estrutura do Projeto

```
python_app/
├── front/
├── src/
├── documents/
├── imagem_logo/
├── imagem_ligacao/
├── tests/
└── main.py
```

---

## ✍️ Autor

Aplicativo desenvolvido por **Asp Of. Eduardo Bezerra Robalinho Dantas da Gama**  
Projeto de graduação em Engenharia Civil – ITA  
Para uso interno no **Centro de Estudos e Projetos de Engenharia (CEPE)** da Força Aérea Brasileira (FAB).

---

## 📜 Licença

Uso restrito ao ambiente institucional da FAB.  
Distribuição externa ou comercialização não autorizada.
