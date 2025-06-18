from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QLabel, QScrollArea, QWidget, QSplitter, QTreeWidget, 
    QTreeWidgetItem, QMessageBox, QFrame
)
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from PySide6.QtCore import Qt
import tempfile
import os
import re
from back.logs import MARCHA_LOG, limpar_marcha
from front.debug_utils import log_info, log_exception

class MarchaCalculoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Marcha de Cálculo - STCAD")
        self.setGeometry(200, 200, 1000, 700)
        self.init_ui()
        self.carregar_marcha()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = QLabel("Marcha de Cálculo Detalhada")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("QLabel { color: #2c3e50; margin: 10px; }")
        layout.addWidget(header)
        
        # Splitter para dividir navegação e conteúdo
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Árvore de navegação (lado esquerdo)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Seções do Cálculo")
        self.tree_widget.setMaximumWidth(300)
        self.tree_widget.itemClicked.connect(self.navegar_para_secao)
        splitter.addWidget(self.tree_widget)
        
        # Área de conteúdo (lado direito)
        self.text_area = QTextEdit()
        self.text_area.setFont(QFont("Consolas", 10))
        self.text_area.setReadOnly(True)
        splitter.addWidget(self.text_area)
        
        # Configurar proporções do splitter
        splitter.setSizes([250, 750])
        layout.addWidget(splitter)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        
        btn_salvar_txt = QPushButton("💾 Salvar como TXT")
        btn_salvar_txt.clicked.connect(self.salvar_como_txt)
        btn_salvar_txt.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        btn_limpar = QPushButton("🧹 Limpar Marcha")
        btn_limpar.clicked.connect(self.limpar_marcha)
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        btn_fechar = QPushButton("❌ Fechar")
        btn_fechar.clicked.connect(self.close)
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        botoes_layout.addWidget(btn_salvar_txt)
        botoes_layout.addWidget(btn_limpar)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_fechar)
        
        layout.addLayout(botoes_layout)
    
    def carregar_marcha(self):
        if not MARCHA_LOG:
            self.text_area.setHtml("""
                <div style='text-align: center; color: #7f8c8d; font-size: 14px; margin-top: 50px;'>
                    <h3>📋 Nenhuma marcha de cálculo disponível</h3>
                    <p>Execute um dimensionamento para gerar a marcha de cálculo.</p>
                </div>
            """)
            return
        
        # Processar e organizar a marcha
        secoes = self.organizar_marcha()
        self.popular_arvore(secoes)
        self.formatar_conteudo_completo()
    
    def organizar_marcha(self):
        """Organiza a marcha em seções baseadas em palavras-chave"""
        secoes = {
            "Configuração Inicial": [],
            "Dimensionamento": [],
            "Verificações": [],
            "Resistências": [],
            "Solicitações": [],
            "Resultados": [],
            "Outros": []
        }
        
        for linha in MARCHA_LOG:
            linha_clean = linha.strip()
            if not linha_clean:
                continue
                
            # Classificar linha baseada em palavras-chave
            if any(palavra in linha_clean.lower() for palavra in ['unidade', 'configuração', 'inicializ']):
                secoes["Configuração Inicial"].append(linha_clean)
            elif any(palavra in linha_clean.lower() for palavra in ['dimensionamento', 'cálculo', 'interação']):
                secoes["Dimensionamento"].append(linha_clean)
            elif any(palavra in linha_clean.lower() for palavra in ['verificação', 'critério', 'aguenta']):
                secoes["Verificações"].append(linha_clean)
            elif any(palavra in linha_clean.lower() for palavra in ['resistência', 'resistencia']):
                secoes["Resistências"].append(linha_clean)
            elif any(palavra in linha_clean.lower() for palavra in ['solicitante', 'solicitação']):
                secoes["Solicitações"].append(linha_clean)
            elif any(palavra in linha_clean.lower() for palavra in ['resultado', 'encontrado', 'sucesso']):
                secoes["Resultados"].append(linha_clean)
            else:
                secoes["Outros"].append(linha_clean)
        
        return secoes
    
    def popular_arvore(self, secoes):
        """Popula a árvore de navegação"""
        self.tree_widget.clear()
        
        for secao, linhas in secoes.items():
            if linhas:  # Só adiciona se tiver conteúdo
                item = QTreeWidgetItem([f"{secao} ({len(linhas)} itens)"])
                item.setData(0, Qt.ItemDataRole.UserRole, secao)
                self.tree_widget.addTopLevelItem(item)
        
        # Adicionar item para ver tudo
        item_completo = QTreeWidgetItem(["📋 Marcha Completa"])
        item_completo.setData(0, Qt.ItemDataRole.UserRole, "completa")
        self.tree_widget.insertTopLevelItem(0, item_completo)
    
    def navegar_para_secao(self, item):
        """Navega para uma seção específica"""
        secao = item.data(0, Qt.ItemDataRole.UserRole)
        
        if secao == "completa":
            self.formatar_conteudo_completo()
        else:
            self.formatar_conteudo_secao(secao)
    
    def formatar_conteudo_completo(self):
        """Formata e exibe todo o conteúdo da marcha"""
        html_content = """
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }
            .header { color: #2c3e50; font-size: 18px; font-weight: bold; margin: 20px 0 10px 0; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            .subheader { color: #34495e; font-size: 14px; font-weight: bold; margin: 15px 0 8px 0; }
            .formula { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; font-family: 'Courier New', monospace; }
            .value { color: #27ae60; font-weight: bold; }
            .warning { color: #e74c3c; font-weight: bold; }
            .success { color: #27ae60; font-weight: bold; }
            .table { background-color: #f8f9fa; padding: 10px; margin: 10px 0; border: 1px solid #bdc3c7; }
        </style>
        <div class="header">📊 Marcha de Cálculo Estrutural - STCAD</div>
        """
        
        for linha in MARCHA_LOG:
            linha_formatada = self.formatar_linha(linha.strip())
            if linha_formatada:
                html_content += linha_formatada
        
        html_content += "</div>"
        self.text_area.setHtml(html_content)
    
    def formatar_conteudo_secao(self, secao):
        """Formata e exibe conteúdo de uma seção específica"""
        secoes = self.organizar_marcha()
        linhas = secoes.get(secao, [])
        
        html_content = f"""
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }}
            .header {{ color: #2c3e50; font-size: 18px; font-weight: bold; margin: 20px 0 10px 0; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
            .formula {{ background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; font-family: 'Courier New', monospace; }}
            .value {{ color: #27ae60; font-weight: bold; }}
            .warning {{ color: #e74c3c; font-weight: bold; }}
            .success {{ color: #27ae60; font-weight: bold; }}
        </style>
        <div class="header">📋 {secao}</div>
        """
        
        for linha in linhas:
            linha_formatada = self.formatar_linha(linha)
            if linha_formatada:
                html_content += linha_formatada
        
        self.text_area.setHtml(html_content)
    
    def formatar_linha(self, linha):
        """Formata uma linha individual da marcha"""
        if not linha:
            return ""
        
        # Detectar e formatar fórmulas matemáticas
        if "=" in linha and any(op in linha for op in ['+', '-', '*', '/', '(', ')']):
            return f'<div class="formula">🧮 {linha}</div>'
        
        # Detectar valores numéricos importantes
        if re.search(r'\d+\.\d+\s*(kN|MPa|mm|pol)', linha):
            return f'<div class="value">📊 {linha}</div>'
        
        # Detectar avisos ou problemas
        if any(palavra in linha.lower() for palavra in ['não aguenta', 'erro', 'falha', 'problema']):
            return f'<div class="warning">⚠️ {linha}</div>'
        
        # Detectar sucessos
        if any(palavra in linha.lower() for palavra in ['sucesso', 'encontrado', 'aguenta']):
            return f'<div class="success">✅ {linha}</div>'
        
        # Detectar cabeçalhos
        if linha.endswith(':') or 'cálculo' in linha.lower() or 'dimensionamento' in linha.lower():
            return f'<div class="subheader">📌 {linha}</div>'
        
        # Linha normal
        return f'<div style="margin: 5px 0;">• {linha}</div>'
    
    def salvar_como_txt(self):
        """Salva a marcha como arquivo TXT"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
                tmp.write("=== MARCHA DE CÁLCULO - STCAD ===\n")
                tmp.write("=" * 50 + "\n\n")
                tmp.writelines(MARCHA_LOG)
                tmp.write("\n" + "=" * 50 + "\n")
                tmp.write("Gerado pelo STCAD - Structural Connections for CAD\n")
                caminho = tmp.name
            
            log_info(f"Marcha de cálculo salva em {caminho}")
            os.startfile(caminho)
            
            QMessageBox.information(
                self, 
                "Arquivo Salvo", 
                f"Marcha de cálculo salva com sucesso!\n\nArquivo: {caminho}\n\nO arquivo foi aberto automaticamente."
            )
            
        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo:\n{str(e)}")
    
    def limpar_marcha(self):
        """Limpa a marcha de cálculo atual"""
        resposta = QMessageBox.question(
            self,
            "Confirmar Limpeza",
            "Tem certeza que deseja limpar a marcha de cálculo atual?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            limpar_marcha()
            self.carregar_marcha()
            QMessageBox.information(self, "Limpeza Concluída", "Marcha de cálculo limpa com sucesso!")
