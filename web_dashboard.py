import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import logging
from flask import Flask, jsonify, request
import json
import base64
from io import BytesIO

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inicialização do servidor Flask e do Dash
server = Flask(__name__)
app = dash.Dash(__name__, server=server)

# Função para criar um DataFrame de exemplo
def create_sample_dataframe():
    """Cria um DataFrame de exemplo para o dashboard."""
    data = {
        'País': ['Brasil', 'Argentina', 'Chile', 'Colômbia', 'México', 'Peru', 'Equador'],
        'PIB (Bilhões USD)': [1800, 450, 280, 350, 1200, 220, 100],
        'População (Milhões)': [215, 45, 19, 52, 126, 33, 18]
    }
    df = pd.DataFrame(data)
    return df

df_sample = create_sample_dataframe()

# Layout do dashboard
app.layout = html.Div(
    style={'backgroundColor': '#f0f2f5', 'fontFamily': 'Arial, sans-serif', 'padding': '20px'},
    children=[
        html.H1(
            "Dashboard Interativo de Exemplo",
            style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}
        ),
        html.Div(
            style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'gap': '20px'},
            children=[
                html.Div(
                    style={'width': '80%', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'},
                    children=[
                        html.H3("Selecione os Dados para o Gráfico", style={'color': '#555'}),
                        dcc.Dropdown(
                            id='dropdown-eixo-x',
                            options=[
                                {'label': 'PIB (Bilhões USD)', 'value': 'PIB (Bilhões USD)'},
                                {'label': 'População (Milhões)', 'value': 'População (Milhões)'}
                            ],
                            value='PIB (Bilhões USD)',
                            style={'width': '100%'}
                        ),
                        dcc.Dropdown(
                            id='dropdown-eixo-y',
                            options=[
                                {'label': 'PIB (Bilhões USD)', 'value': 'PIB (Bilhões USD)'},
                                {'label': 'População (Milhões)', 'value': 'População (Milhões)'}
                            ],
                            value='População (Milhões)',
                            style={'width': '100%', 'marginTop': '10px'}
                        )
                    ]
                ),
                html.Div(
                    style={'width': '80%', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'},
                    children=[
                        dcc.Graph(
                            id='grafico-dinamico'
                        )
                    ]
                )
            ]
        )
    ]
)

# Callback para atualizar o gráfico
@app.callback(
    Output('grafico-dinamico', 'figure'),
    [Input('dropdown-eixo-x', 'value'),
     Input('dropdown-eixo-y', 'value')]
)
def update_graph(eixo_x, eixo_y):
    """Atualiza o gráfico com base nas seleções do usuário."""
    logging.info(f"Atualizando gráfico com X='{eixo_x}' e Y='{eixo_y}'")
    fig = px.bar(
        df_sample,
        x=eixo_x,
        y=eixo_y,
        color='País',
        title=f"Gráfico de {eixo_y} versus {eixo_x}",
        height=500
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='#333',
        title_font_size=20
    )
    return fig

@server.route('/api/plot_data', methods=['POST'])
def get_plot_data():
    try:
        data = request.get_json()
        logging.info(f"Dados recebidos para plotagem: {data}")
        
        # Simula a criação de um gráfico com base nos dados
        df = pd.DataFrame(data['data'])
        x_col = data['x_column']
        y_col = data['y_column']
        
        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            title=f"Gráfico de {y_col} versus {x_col}",
            height=400
        )
        
        # Converte o gráfico para HTML
        plot_html = fig.to_html(full_html=False, include_plotlyjs=False)
        return jsonify({'plot_html': plot_html})

    except Exception as e:
        # Catch any errors during the process and return an error message
        logging.error(f"Σφάλμα κατά τη δημιουργία του γραφήματος: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8050, debug=True)
