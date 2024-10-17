# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


from dash import Dash, dcc, html, Input, Output, Patch, callback, State
import pandas as pd
import json
from data_functions import *
from style_sheet import *

app = Dash(__name__)


mobile = first_setup()

Landkreise = mobile[mobile['Verwaltungsebene']=='3 - Kreis']['Name'] #[['code_fill','Name']].set_index('code_fill').to_dict()['Name']
Gemeinden = mobile[mobile['Verwaltungsebene']=='4 - Gemeinde']['Name'] #[['code_fill','Name']].set_index('code_fill').to_dict()['Name']

# Define app layout
app.layout = html.Div([

    html.H3(children='Daten-Generator', style=text_style),
    #html.Img(src='data/external/bydata_logo_wordmark_medium.svg'),
    # Radio items with two options
    dcc.RadioItems(
        id='radio-selection',
        options=[
            {'label': 'Stadt/Gemeinde', 'value': 'opt1'},
            {'label': 'Landkreis/Kreisfreie Stadt', 'value': 'opt2'}
        ],
        value='opt1'  # Default value
    ),
    
    # Dropdown which will have options based on radio item selection
    dcc.Dropdown(
        id='dropdown-selection',
        multi=True,
        style=question_style
    ),
    html.Div([html.Br(), html.Br()], style=question_style),
    html.Button(id='submit-button', n_clicks=0, children='Daten erzeugen', style=button_style),

    # Output component to show selected dropdown value (optional)
    html.Div(id='output1'),
    html.Div([html.Br(), html.Br()]),
    html.Div(id='output2'),
])

# Callback to update the Dropdown options based on selected RadioItem
@app.callback(
    Output('dropdown-selection', 'options'),
    Input('radio-selection', 'value')
)
def set_dropdown_options(selected_radio):
    if selected_radio == 'opt1':
        return Gemeinden
    elif selected_radio == 'opt2':
        return Landkreise

@app.callback(
    Output('output1', 'children'),
    Output('output2', 'children'),
    Input('submit-button','n_clicks'),
    State('dropdown-selection','value'),
)
def data_processing(n_clicks, selection):
    if n_clicks > 0:
        try:
            code = mobile[mobile['Name']==selection[0]].reset_index()['code_fill'][0]

            export_1 = energy_data(code)
            export_2 = kfz_data(code)
            export_3 = population_data(code)
            export_4 = mobile_data(code, mobile)

            data_export = {
                "Name": selection[0], 
                "Energie": export_1, 
                "KFZ": export_2, 
                "Bevoelkerung": export_3, 
                "Mobilfunk": export_4
            }

            # Convert data_export dictionary to JSON string
            json_dump = json.dumps(data_export, ensure_ascii=False)

            # Replace XML special characters
            json_dump = json_dump.replace('&', '&amp;')

            return f'Daten für Auswahl "{selection[0]}" wurden erfolgreich erstellt.', json_dump
        except Exception as error:
            return f'Auswahl: "{selection[0]}" --- Error: {error}', ''


if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=False)
    #app.run(debug=False)
