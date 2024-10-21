# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output, callback, State
import pandas as pd
import json
import data_functions as df
import repo_functions as rf
import style_sheet as css

app = Dash(__name__)
app.config.suppress_callback_exceptions = True

mobile = df.first_setup()

Landkreise = [{'label': name, 'value': name} for name in mobile[mobile['Verwaltungsebene'] == '3 - Kreis']['Name']]
Gemeinden = [{'label': name, 'value': name} for name in mobile[mobile['Verwaltungsebene'] == '4 - Gemeinde']['Name']]

# Define app layout
app.layout = html.Div([
    html.H3(children='Daten-Generator', style=css.text_style),
    dcc.RadioItems(
        id='radio-selection',
        options=[
            {'label': 'Stadt/Gemeinde', 'value': 'opt1'},
            {'label': 'Landkreis/Kreisfreie Stadt', 'value': 'opt2'}
        ],
        value='opt1'
    ),
    dcc.Dropdown(
        id='dropdown-selection',
        multi=True,
        style=css.question_style
    ),
    html.Div([html.Br(), html.Br()], style=css.question_style),

    # Checkbox for automatic catalog transfer
    html.Div([
        dcc.Checklist(
            id='auto-transfer-checkbox',
            options=[{'label': 'Daten automatisch in Katalog übertragen', 'value': 'auto_transfer'}],
            value=[]  # Unchecked by default
        ),
        html.Div(id='catalog-options', children=[], style={'display': 'none'}),
    ], style=css.question_style),

    html.Button(id='submit-button', n_clicks=0, children='Daten erzeugen', style=css.button_style),
    html.Div(id='output1'),
    html.Div([html.Br(), html.Br()]),
    html.Div(id='output2'),

    # Hidden store to hold dynamic input states
    dcc.Store(id='catalog-id-store'),
    dcc.Store(id='environment-store'),
])


# Callback to update the Dropdown options based on selected RadioItem
@app.callback(
    Output('dropdown-selection', 'options'),
    Input('radio-selection', 'value')
)
def set_dropdown_options(selected_radio):
    options = Gemeinden if selected_radio == 'opt1' else Landkreise
    return options


# Callback to dynamically show/hide catalog options and update states
@app.callback(
    Output('catalog-options', 'style'),
    Output('catalog-options', 'children'),
    Output('catalog-id-store', 'data'),
    Output('environment-store', 'data'),
    Input('auto-transfer-checkbox', 'value'),
    State('catalog-id-store', 'data'),
    State('environment-store', 'data')
)
def toggle_catalog_options(checklist_value, catalog_id_store, environment_store):
    if 'auto_transfer' in checklist_value:
        return (
            {'display': 'block'},
            [
                html.Label('Katalog-ID: '),
                dcc.Input(id='catalog-id', type='text'),
                html.Br(),
                html.Label('Umgebung: '),
                dcc.Dropdown(
                    id='environment-dropdown',
                    options=[
                        {'label': 'open', 'value': 'open'},
                        {'label': 'staging', 'value': 'staging'}
                    ],
                    value='open'
                )
            ],
            catalog_id_store,
            environment_store
        )
    else:
        return {'display': 'none'}, [], catalog_id_store, environment_store


# Callback to update input values into store
@app.callback(
    Output('catalog-id-store', 'data', allow_duplicate=True),
    Output('environment-store', 'data', allow_duplicate=True),
    Input('catalog-id', 'value'),
    Input('environment-dropdown', 'value'),
    prevent_initial_call=True
)
def update_stores_from_inputs(catalog_id_value, environment_value):
    return catalog_id_value, environment_value


# Enhanced processing callback
@app.callback(
    Output('output1', 'children'),
    Output('output2', 'children'),
    Input('submit-button', 'n_clicks'),
    State('dropdown-selection', 'value'),
    State('auto-transfer-checkbox', 'value'),
    State('catalog-id-store', 'data'),
    State('environment-store', 'data')
)
def data_processing(n_clicks, selection, auto_transfer, catalog_id_store, environment_store):
    if n_clicks > 0:
        try:
            if not selection:
                raise ValueError("Es wurde keine Auswahl getroffen.")

            code = mobile[mobile['Name'] == selection[0]].reset_index()['code_fill'][0]

            export_1 = df.energy_data(code)
            export_2 = df.kfz_data(code)
            export_3 = df.population_data(code)
            export_4 = df.mobile_data(code, mobile)

            data_export = {
                "Name": selection[0],
                "Energie": export_1,
                "KFZ": export_2,
                "Bevoelkerung": export_3,
                "Mobilfunk": export_4
            }

            json_dump = json.dumps(data_export, ensure_ascii=False)
            json_dump = json_dump.replace('&', '&amp;')

            message = f'Daten für Auswahl "{selection[0]}" wurden erfolgreich erstellt.'

            if 'auto_transfer' in auto_transfer:
                if not catalog_id_store or not environment_store:
                    raise ValueError("Katalog-ID oder Umgebung fehlen.")
                catalog_status = rf.set_catalog_viz_data(data_export, catalog_id_store, environment_store)
                message += f' Katalog-Übertragungsstatus: {catalog_status}'

            print(message)
            return message, json_dump
        except Exception as error:
            print(f"Error occurred: {error}")
            return f'Auswahl: "{selection[0]}" --- Error: {error}', ''


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
    # app.run(debug=False)
