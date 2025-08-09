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

# Ρύθμιση της καταγραφής (logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Αρχικοποίηση του Flask server και του Dash
server = Flask(__name__)
app = dash.Dash(__name__, server=server)

# Συνάρτηση για τη δημιουργία ενός DataFrame παραδείγματος
def create_sample_dataframe():
    """Δημιουργεί ένα DataFrame παραδείγματος για το dashboard."""
    data = {
        'Χώρα': ['Ελλάδα', 'Γερμανία', 'Γαλλία', 'Ισπανία', 'Ιταλία', 'Πορτογαλία', 'Κύπρος'],
        'ΑΕΠ (Δισεκατομμύρια USD)': [210, 4200, 2900, 1400, 2100, 250, 25],
        'Πληθυσμός (Εκατομμύρια)': [10.5, 83, 65, 47, 60, 10.2, 0.9]
    }
    df = pd.DataFrame(data)
    return df

df_sample = create_sample_dataframe()

# Διάταξη (Layout) του dashboard
app.layout = html.Div(
    style={'backgroundColor': '#f0f2f5', 'fontFamily': 'Arial, sans-serif', 'padding': '20px'},
    children=[
        html.H1(
            "Διαδραστικό Dashboard Παραδείγματος",
            style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}
        ),
        html.Div(
            style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'gap': '20px'},
            children=[
                html.Div(
                    style={'width': '80%', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'},
                    children=[
                        html.H3("Επιλέξτε Δεδομένα για το Γράφημα", style={'color': '#555'}),
                        dcc.Dropdown(
                            id='dropdown-eixo-x',
                            options=[
                                {'label': 'ΑΕΠ (Δισεκατομμύρια USD)', 'value': 'ΑΕΠ (Δισεκατομμύρια USD)'},
                                {'label': 'Πληθυσμός (Εκατομμύρια)', 'value': 'Πληθυσμός (Εκατομμύρια)'}
                            ],
                            value='ΑΕΠ (Δισεκατομμύρια USD)',
                            style={'width': '100%'}
                        ),
                        dcc.Dropdown(
                            id='dropdown-eixo-y',
                            options=[
                                {'label': 'ΑΕΠ (Δισεκατομμύρια USD)', 'value': 'ΑΕΠ (Δισεκατομμύρια USD)'},
                                {'label': 'Πληθυσμός (Εκατομμύρια)', 'value': 'Πληθυσμός (Εκατομμύρια)'}
                            ],
                            value='Πληθυσμός (Εκατομμύρια)',
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

# Callback για την ενημέρωση του γραφήματος
@app.callback(
    Output('grafico-dinamico', 'figure'),
    [Input('dropdown-eixo-x', 'value'),
     Input('dropdown-eixo-y', 'value')]
)
def update_graph(eixo_x, eixo_y):
    """Ενημερώνει το γράφημα με βάση τις επιλογές του χρήστη."""
    logging.info(f"Ενημέρωση γραφήματος με X='{eixo_x}' και Y='{eixo_y}'")
    fig = px.bar(
        df_sample,
        x=eixo_x,
        y=eixo_y,
        color='Χώρα',
        title=f"Γράφημα {eixo_y} έναντι {eixo_x}",
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
        logging.info(f"Ελήφθησαν δεδομένα για το γράφημα: {data}")
        
        # Προσομοίωση δημιουργίας γραφήματος με βάση τα δεδομένα
        df = pd.DataFrame(data['data'])
        x_col = data['x_column']
        y_col = data['y_column']
        
        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            title=f"Γράφημα {y_col} έναντι {x_col}",
            height=400
        )
        
        # Μετατροπή του γραφήματος σε HTML
        plot_html = fig.to_html(full_html=False, include_plotlyjs=False)
        return jsonify({'plot_html': plot_html})

    except Exception as e:
        # Χειρισμός σφαλμάτων κατά τη διαδικασία και επιστροφή μηνύματος σφάλματος
        logging.error(f"Σφάλμα κατά τη δημιουργία του γραφήματος: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8050, debug=True)
