import base64
import json
from typing import List, Dict

import dash
import visdcc
from dash import html, callback, Input, Output, State, ALL, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
import pandas as pd
import io
import os

from py_arg.abstract_argumentation_classes.abstract_argumentation_framework import AbstractArgumentationFramework
from py_arg.generators.abstract_argumentation_framework_generators.abstract_argumentation_framework_generator import \
    AbstractArgumentationFrameworkGenerator
from py_arg.import_export.argumentation_framework_from_aspartix_format_reader import \
    ArgumentationFrameworkFromASPARTIXFormatReader
from py_arg.import_export.argumentation_framework_from_iccma23_format_reader import \
    ArgumentationFrameworkFromICCMA23FormatReader
from py_arg.import_export.argumentation_framework_from_json_reader import ArgumentationFrameworkFromJsonReader
from py_arg.import_export.argumentation_framework_from_trivial_graph_format_reader import \
    ArgumentationFrameworkFromTrivialGraphFormatReader
from py_arg.import_export.argumentation_framework_to_aspartix_format_writer import \
    ArgumentationFrameworkToASPARTIXFormatWriter
from py_arg.import_export.argumentation_framework_to_iccma23_format_writer import \
    ArgumentationFrameworkToICCMA23FormatWriter
from py_arg.import_export.argumentation_framework_to_json_writer import ArgumentationFrameworkToJSONWriter
from py_arg.import_export.argumentation_framework_to_trivial_graph_format_writer import \
    ArgumentationFrameworkToTrivialGraphFormatWriter
from py_arg_visualisation.functions.explanations_functions.explanation_function_options import \
    EXPLANATION_FUNCTION_OPTIONS
from py_arg_visualisation.functions.explanations_functions.get_af_explanations import \
    get_argumentation_framework_explanations
from py_arg_visualisation.functions.extensions_functions.get_accepted_arguments import get_accepted_arguments
from py_arg_visualisation.functions.extensions_functions.get_af_extensions import get_argumentation_framework_extensions
from py_arg_visualisation.functions.graph_data_functions.get_af_graph_data import get_argumentation_framework_graph_data
from py_arg_visualisation.functions.import_functions.read_argumentation_framework_functions import \
    read_argumentation_framework

dash.register_page(__name__, name='Visualise', title='Visualise')


# Create layout elements and compose them into the layout for this page.

def get_abstract_setting_specification_div():
    return html.Div(children=[
        dcc.Store(id='selected-argument-store-abstract'),
        dbc.Col([
            dbc.Row([dbc.Col([dbc.DropdownMenu(
                                label="Choose a Topic",
                                children=[
                                    dbc.DropdownMenuItem("Racism", id="racism"),
                                    dbc.DropdownMenuItem("Economy", id="economy"),
                                    dbc.DropdownMenuItem("Climate Change", id="climate-change"),
                                    dbc.DropdownMenuItem("Supreme Court", id="supreme-court"),
                                    dbc.DropdownMenuItem("Minimum Wage", id="minimum-wage"),
                                    dbc.DropdownMenuItem("COVID", id="covid"),
                                    dbc.DropdownMenuItem("Healthcare", id="healthcare"),
                                    dbc.DropdownMenuItem("National Security", id="national-security"),
                                    dbc.DropdownMenuItem("Why They Should Be Elected", id="why-they-should-be-elected"),
                                    dbc.DropdownMenuItem("Democracy", id="democracy"),
                                    dbc.DropdownMenuItem("Integrity", id="integrity"),
                                ],
                                id="dropdown-menu",
                                className="mb-2"
                                ),
                                html.Div(id='output-dropdown')
                            ], width=4),
                     dbc.Col(dcc.Upload(dbc.Button('Add argument', className='w-100'), id='upload-af')),
                     dbc.Col(dcc.Upload(dbc.Button('Add relationship', className='w-100'), id='upload-af'))
                     ], className='mt-2'),
            dbc.Row([
                dbc.Col(dbc.Checklist(
                    id='checkbox',
                    options=[
                        {'label': 'Attack', 'value': 'attack'},
                        {'label': 'Support', 'value': 'support'}
                    ],
                    value=['attack'],  # Default selected values
                    inline=True  # To display options in a single line
                ), width=6),
                dbc.Col(html.Div(id='output-checkbox'), width=6)
            ], className="mt-4"),
            dbc.Row([dbc.Col(dbc.Button('Display', id='generate-random-af-button', n_clicks=0,
                                        className='w-100')),
                     ], className='mt-2'),
            dbc.Row([
                dbc.Col([
                    html.B('Arguments'),
                    dbc.Textarea(id='abstract-arguments',
                                 placeholder='Add one argument per line. For example:\n A\n B\n C',
                                 value='', style={'height': '0px'})
                ]),
                dbc.Col([
                    html.B('Attacks'),
                    dbc.Textarea(id='abstract-attacks',
                                 placeholder='Add one attack per line. For example: \n (A,B) \n (A,C) \n (C,B)',
                                 value='', style={'height': '0px'}),
                ])
            ], className='mt-22'),
            dbc.Row([
                dbc.InputGroup([
                    dbc.InputGroupText('Filename'),
                    dbc.Input(value='edited_af', id='21-af-filename'),
                    dbc.InputGroupText('.'),
                    dbc.Select(options=[{'label': extension, 'value': extension}
                                        for extension in ['JSON', 'TGF', 'APX', 'ICCMA23']],
                               value='JSON', id='21-af-extension'),
                    dbc.Button('Download', id='21-af-download-button'),
                ], className='mt-2'),
                dcc.Download(id='21-af-download')
            ]),
            dbc.Row([
                dbc.Col([
                    html.H1("Explanation :"),
                    html.Div(id='node-click-message')
                ])
            ])
        ])
    ])


def get_abstract_evaluation_div():
    return html.Div([
        dbc.Col([
            
                dbc.Row([
                    dbc.Col(html.B('Semantics')),
                    dbc.Col(dbc.Select(options=[
                        {'label': 'Admissible', 'value': 'Admissible'},
                        {'label': 'Complete', 'value': 'Complete'},
                        {'label': 'Grounded', 'value': 'Grounded'},
                        {'label': 'Preferred', 'value': 'Preferred'},
                        {'label': 'Ideal', 'value': 'Ideal'},
                        {'label': 'Stable', 'value': 'Stable'},
                        {'label': 'Semi-stable', 'value': 'SemiStable'},
                        {'label': 'Eager', 'value': 'Eager'},
                    ], value='Complete', id='abstract-evaluation-semantics')),
                ]),

                dbc.Row([
                    dbc.Col(html.B('Evaluation strategy')),
                    dbc.Col(dbc.Select(
                        options=[
                            {'label': 'Credulous', 'value': 'Credulous'},
                            {'label': 'Skeptical', 'value': 'Skeptical'}
                        ], value='Credulous', id='abstract-evaluation-strategy')),
                ]),
                dbc.Row(id='abstract-evaluation')
            
        ])
    ])


def get_abstract_explanation_div():
    return html.Div([
        dbc.Row([
            dbc.Col(html.B('Type')),
            dbc.Col(dbc.Select(options=[{'label': 'Acceptance', 'value': 'Acceptance'},
                                        {'label': 'Non-Acceptance', 'value': 'NonAcceptance'}],
                               value='Acceptance', id='abstract-explanation-type'))]),
        dbc.Row([
            dbc.Col(html.B('Explanation function')),
            dbc.Col(dbc.Select(id='abstract-explanation-function'))
        ]),
        dbc.Row(id='abstract-explanation')
    ])


left_column = dbc.Col(
    dbc.Accordion([
        dbc.AccordionItem(get_abstract_setting_specification_div(), title='Abstract Argumentation Framework'),
        dbc.AccordionItem(get_abstract_evaluation_div(), title='Evaluation', item_id='Evaluation'),
        dbc.AccordionItem(get_abstract_explanation_div(), title='Explanation', item_id='Explanation')
    ], id='abstract-evaluation-accordion')
)
right_column = dbc.Col([
    dbc.Row([
        dbc.Card(visdcc.Network(data={'nodes': [], 'edges': []}, id='abstract-argumentation-graph',
                                options={'height': '500px'}), body=True),
    ]),
    dbc.Row([
        html.Div(id='legend-colors')
    ])
])
layout_abstract = dbc.Row([left_column, right_column])
layout = html.Div([html.H1('Visualisation of abstract argumentation frameworks'), layout_abstract])


@callback(
    Output('output-dropdown', 'children'),
    [Input('racism', 'n_clicks'),
     Input('economy', 'n_clicks'),
     Input('climate-change', 'n_clicks'),
     Input('supreme-court', 'n_clicks'),
     Input('minimum-wage', 'n_clicks'),
     Input('covid', 'n_clicks'),
     Input('healthcare', 'n_clicks'),
     Input('national-security', 'n_clicks'),
     Input('why-they-should-be-elected', 'n_clicks'),
     Input('democracy', 'n_clicks'),
     Input('integrity', 'n_clicks')]
)
def update_output(*args):
    ctx = dash.callback_context

    if not ctx.triggered:
        return 'No topic selected'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    topic_dict = {
        "racism": "Racism",
        "economy": "Economy",
        "climate-change": "Climate Change",
        "supreme-court": "Supreme Court",
        "minimum-wage": "Minimum Wage",
        "covid": "COVID",
        "healthcare": "Healthcare",
        "national-security": "National Security",
        "why-they-should-be-elected": "Why They Should Be Elected",
        "democracy": "Democracy",
        "integrity": "Integrity"
    }

    return topic_dict.get(button_id, 'No topic selected')

def replace_spaces(argument):
    return argument.replace(" ", "_").replace(",", ";")

@callback(
    Output('abstract-arguments', 'value'),
    Output('abstract-attacks', 'value'),
    Input('generate-random-af-button', 'n_clicks'),
    Input('upload-af', 'contents'),
    State('upload-af', 'filename'),
    State('output-dropdown', 'children'),
    State('checkbox', 'value')
)
def generate_abstract_argumentation_framework(_nr_of_clicks_random: int, af_content: str, af_filename: str, topic: str, checkbox_values: list):
    """
    Generate a random AF after clicking the button and put the result in the text box.
    """
    if dash.callback_context.triggered_id == 'generate-random-af-button':
        if topic == 'Racism':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                   # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'Economy':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'Climate Change':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'Supreme Court':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'Minimum Wage':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'COVID':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value
        
        if topic == 'Healthcare':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'National Security':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'Why They Should Be Elected':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value

        if topic == 'Democracy':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value
        
        if topic == 'Integrity':
            l=[]
            h=[]
            if 'attack' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_attack.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)

                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

         
                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$A$({argument_5},{argument_6})')
                
            if 'support' in checkbox_values:
                # Construire le chemin du fichier CSV de manière dynamique
                base_path = os.path.dirname(__file__)
                file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_support.csv')
                # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                df = pd.read_csv(file_path, skiprows=0)
                
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]
                    # Remplacer les espaces par des tirets
                    argument_5 = replace_spaces(argument_5)
                    argument_6 = replace_spaces(argument_6)

                    # Vérifier si les éléments ne sont pas déjà présents dans la première liste de random_af
                    if argument_5 not in l:
                        l.append(argument_5)
                    if argument_6 not in l:
                        l.append(argument_6)

                    # Ajouter la relation entre les éléments à la deuxième liste de random_af
                    h.append(f'$S$({argument_5},{argument_6})')
            
            # Suppose que random_af est un objet AbstractArgumentationFramework avec des attributs arguments et defeats
            abstract_arguments_value = '$end$'.join((str(arg) for arg in l))
            # Construction de la représentation des attaques en utilisant les éléments de defeats
            abstract_attacks_value = '$end$'.join((str(defeat)for defeat in h) )
            return abstract_arguments_value, abstract_attacks_value
    return '', ''



def add_newline_every_n_chars(text: str, n: int) -> str:
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        # Vérifier si ajouter le mot actuel dépasse la longueur n
        if len(current_line) + len(word) + 1 > n:
            # Ajouter la ligne actuelle à la liste des lignes
            lines.append(current_line)
            # Commencer une nouvelle ligne avec le mot actuel
            current_line = word
        else:
            # Ajouter le mot à la ligne actuelle
            if current_line:
                current_line += " " + word
            else:
                current_line = word

    # Ajouter la dernière ligne
    if current_line:
        lines.append(current_line)
    
    # Joindre les lignes avec '\n'
    return '\n'.join(lines)
def replace_spaces2(argument):
    return argument.replace("_", " ").replace(";", ",")
def replace_fin(argument):
    return argument.replace("\n\n", "$end$")
def replace_mid(argument):
    return argument.replace(",", "$,$")
from py_arg.abstract_argumentation_classes.argument import Argument
from py_arg.abstract_argumentation_classes.defeat import Defeat


def create_legend_colors(colors: list, speakers: list):
    elements = []
    for i in range(len(speakers)):
        elements.append(html.H3(speakers[i], style={'color': colors[i]}))
    return elements

@callback(
    Output('abstract-argumentation-graph', 'data'),
    Output('legend-colors', 'children'),
    Input('abstract-arguments', 'value'),
    Input('abstract-attacks', 'value'),
    Input('selected-argument-store-abstract', 'data'),
    State('color-blind-mode', 'on'),
    State('output-dropdown', 'children'),
    State('checkbox', 'value'),
    prevent_initial_call=True
)
def create_abstract_argumentation_framework(arguments: str, attacks: str,
                                            selected_arguments: Dict[str, List[str]],
                                            color_blind_mode: bool, 
                                            topic: str, 
                                            checkbox_values: list):
    """
    Send the AF data to the graph for plotting.
    """
    arguments=replace_fin(replace_spaces2(arguments))
    attacks=replace_fin(replace_spaces2(replace_mid(attacks)))

    try:
        arg_list = [Argument(arg) for arg in arguments.split("$end$")]
        defeat_list = []
        for attack in attacks.split('$end$'):
            att_list = attack.replace(')', '').replace('(', '').replace('$A$', '').replace('$S$', '').split("$,$")     
            if len(att_list) == 2 and att_list[0] != '' and att_list[1] != '':
                from_argument = Argument(att_list[0])
                to_argument = Argument(att_list[1])
                if from_argument not in arg_list or to_argument not in arg_list:
                    raise ValueError('Not a valid defeat, since one of the arguments does not exist.')
                defeat_list.append(Defeat(Argument(att_list[0]), Argument(att_list[1])))

        arg_framework = AbstractArgumentationFramework('AF', arg_list, defeat_list)
        #arg_framework = read_argumentation_framework(arguments, attacks)
    except ValueError:
        arg_framework = AbstractArgumentationFramework()

    if dash.callback_context.triggered_id != 'selected-argument-store-abstract':
        selected_arguments = None
    
    data = get_argumentation_framework_graph_data(arg_framework, selected_arguments, color_blind_mode)

    colors=['blue','red','green','yellow']
    legend_elements=[]

    if topic == 'Racism':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match
                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]

                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]
                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2        
                
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match
                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]

                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]
                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)
    
    if topic == 'Economy':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_econemy_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match
                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]

                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]
                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match
                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]

                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]
                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)
    
    if topic == 'Climate Change':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'Supreme Court':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)
    
    if topic == 'Minimum Wage':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'COVID':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'Healthcare':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'National Security':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'Why They Should Be Elected':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'Democracy':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    if topic == 'Integrity':
        if 'attack' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_attack.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        if 'support' in checkbox_values:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_support.csv')
            # Lire les données du fichier CSV en sautant la première ligne (l'entête)
            df = pd.read_csv(file_path, skiprows=0)
            l=[]
            for i in range(len(data['nodes'])):
                for index, row in df.iterrows():
                    # Extraire les éléments de la 5ème et 6ème colonne
                    argument_5 = row.iloc[4]
                    argument_6 = row.iloc[5]

                    argument_7 = row.iloc[6]
                    argument_8 = row.iloc[7]
                    
                    couleur1 = 'gray'  # default color if no match
                    couleur2 = 'gray'  # default color if no match

                    if argument_7 not in l:
                        couleur1=colors[len(l)]
                        l.append(argument_7)
                    else:
                        couleur1 = colors[l.index(argument_7)]
                    if argument_8 not in l:
                        couleur2=colors[len(l)]
                        l.append(argument_8)
                    else:
                        couleur2 = colors[l.index(argument_8)]

                    if data['nodes'][i]['id'] == argument_5:
                        data['nodes'][i]['color']=couleur1
                    if data['nodes'][i]['id'] == argument_6:
                        data['nodes'][i]['color']=couleur2
        legend_elements=create_legend_colors(colors,l)

    for i in range(len(data['nodes'])):
        lab = ''
        for j in range(len(data['nodes'][i]['label'])):
            lab=lab+data['nodes'][i]['label'][j]
            if j%60==0 and j!=0:
                if data['nodes'][i]['label'][j+1]!=' ' and data['nodes'][i]['label'][j]!=' ':
                    lab=lab+'-'
                lab=lab+'\n' 
        data['nodes'][i]['label']=lab
    
    return data,legend_elements


@callback(
    Output('node-click-message', 'children'),
    Input('abstract-argumentation-graph', 'selection'),
    Input('upload-af', 'contents'),
    State('upload-af', 'filename'),
    State('output-dropdown', 'children'),
    State('checkbox', 'value')
)
def display_click_data(selection, af_content: str, af_filename: str, topic: str,checkbox_values: list):
    if selection:
        node_id = selection['nodes'][0] if selection['nodes'] else None
        if node_id is not None:
            if topic == 'Racism':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Economy':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)
            
            if topic == 'Climate Change':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Supreme Court':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Minimum Wage':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'COVID':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)
            
            if topic == 'Healthcare':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'National Security':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Why They Should Be Elected':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Democracy':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Integrity':
                elements = []
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    att_list=[]
                    att_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            att_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            att_by_list.append(row.iloc[3])
                    if att_list:
                        elements.append(html.H3("Attack : "))
                        for item in att_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if att_by_list:
                        elements.append(html.H3("Attacked by : "))
                        for item in att_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    sup_list=[]
                    sup_by_list=[]
                    for index, row in df.iterrows():
                        if row.iloc[4] == node_id:
                            sup_list.append(row.iloc[3])
                        if row.iloc[5] == node_id:
                            sup_by_list.append(row.iloc[3])
                    if sup_list:
                        elements.append(html.H3("Support : "))
                        for item in sup_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                    if sup_by_list:
                        elements.append(html.H3("Supported by : "))
                        for item in sup_by_list:
                            elements.append(html.P(item))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)



        edge_id = selection['edges'][0] if selection['edges'] else None
        if edge_id is not None:
            elements = []
            elements.append(html.H3("Relationship : "))
            if topic == 'Racism': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_racism_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Economy': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_economy_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)
            
            if topic == 'Climate Change': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_climate_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)
            
            if topic == 'Supreme Court': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_court_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Minimum Wage': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_wage_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'COVID': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_covid_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Healthcare': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_healthcare_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'National Security': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_security_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Why They Should Be Elected': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_elected_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Democracy': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_democracy_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)

            if topic == 'Integrity': 
                if 'attack' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_attack.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                if 'support' in checkbox_values:
                    base_path = os.path.dirname(__file__)
                    file_path = os.path.join(base_path, '..', 'data', 'full_dataset_processing_integrity_support.csv')
                    # Lire les données du fichier CSV en sautant la première ligne (l'entête)
                    df = pd.read_csv(file_path, skiprows=0)
                    for index, row in df.iterrows():
                        rela=row.iloc[4]+"-"+row.iloc[5]
                        if rela == edge_id :
                            elements.append(html.P(row.iloc[3]))
                            elements.append(html.P("\n\n"))
                return dbc.Row(elements)
            
    return 'Click on a node/edge to see the explanation.'


@callback(
    Output('21-af-download', 'data'),
    Input('21-af-download-button', 'n_clicks'),
    State('abstract-arguments', 'value'),
    State('abstract-attacks', 'value'),
    State('21-af-filename', 'value'),
    State('21-af-extension', 'value'),
    prevent_initial_call=True,
)
def download_generated_abstract_argumentation_framework(
        _nr_clicks: int, arguments_text: str, defeats_text: str, filename: str, extension: str):
    argumentation_framework = read_argumentation_framework(arguments_text, defeats_text)

    if extension == 'JSON':
        argumentation_framework_json = ArgumentationFrameworkToJSONWriter().to_dict(argumentation_framework)
        argumentation_framework_str = json.dumps(argumentation_framework_json)
    elif extension == 'TGF':
        argumentation_framework_str = \
            ArgumentationFrameworkToTrivialGraphFormatWriter.write_to_str(argumentation_framework)
    elif extension == 'APX':
        argumentation_framework_str = \
            ArgumentationFrameworkToASPARTIXFormatWriter.write_to_str(argumentation_framework)
    elif extension == 'ICCMA23':
        argumentation_framework_str = \
            ArgumentationFrameworkToICCMA23FormatWriter.write_to_str(argumentation_framework)
    else:
        raise NotImplementedError

    return {'content': argumentation_framework_str, 'filename': filename + '.' + extension}


@callback(
    Output('abstract-evaluation', 'children'),
    State('abstract-arguments', 'value'),
    State('abstract-attacks', 'value'),
    Input('abstract-evaluation-accordion', 'active_item'),
    Input('abstract-evaluation-semantics', 'value'),
    Input('abstract-evaluation-strategy', 'value'),
    prevent_initial_call=True
)
def evaluate_abstract_argumentation_framework(arguments: str, attacks: str,
                                              active_item: str,
                                              semantics: str, strategy: str):
    if active_item != 'Evaluation':
        raise PreventUpdate

    arg_list = [Argument(arg) for arg in arguments.split("$end$")]
    defeat_list_att = []
    defeat_list_sup = []
    for attack in attacks.split('$end$'):
        if attack[:3]=='$A$':
            att_list = attack.replace(')', '').replace('(', '').replace('$A$', '').split(",")   
            if len(att_list) == 2 and att_list[0] != '' and att_list[1] != '':
                from_argument = Argument(att_list[0])
                to_argument = Argument(att_list[1])
                if from_argument not in arg_list or to_argument not in arg_list:
                    raise ValueError('Not a valid defeat, since one of the arguments does not exist.')
                defeat_list_att.append(Defeat(Argument(att_list[0]), Argument(att_list[1])))
        if attack[:3]=='$S$':
            sup_list = attack.replace(')', '').replace('(', '').replace('$S$', '').split(",")   
            if len(sup_list) == 2 and sup_list[0] != '' and sup_list[1] != '':
                from_argument = Argument(sup_list[0])
                to_argument = Argument(sup_list[1])
                if from_argument not in arg_list or to_argument not in arg_list:
                    raise ValueError('Not a valid defeat, since one of the arguments does not exist.')
                defeat_list_sup.append(Defeat(Argument(sup_list[0]), Argument(sup_list[1])))


    new_arg_list = []
    defeat_list = []
    for arg in arg_list:
        n=0
        for i in range(len(defeat_list_att)):
            #print('defeat_list_att[i].to_argument')
            #print(defeat_list_att[i].to_argument)
            if arg == defeat_list_att[i].to_argument:
                n=n-1
        for i in range(len(defeat_list_sup)):
            if arg == defeat_list_sup[i].to_argument:
                n=n+1
        if n>=0:
            new_arg_list.append(arg)
            for i in range(len(defeat_list_att)):
                if arg == defeat_list_att[i].to_argument or arg == defeat_list_att[i].from_argument:
                    defeat_list.append(defeat_list_att[i])
            for i in range(len(defeat_list_sup)):
                if arg == defeat_list_sup[i].to_argument or arg == defeat_list_sup[i].from_argument:
                    defeat_list.append(defeat_list_sup[i])
                        
    
    #defeat_list=defeat_list_att+defeat_list_sup
    arg_framework = AbstractArgumentationFramework('AF', arg_list, defeat_list)
    # Read the abstract argumentation framework.
    #arg_framework = read_argumentation_framework(arguments, attacks)
    print('arg_framework')
    print(arg_framework)
    #create_abstract_argumentation_framework(arg_framework.arguments, arg_framework.defeats,)

    # Compute the extensions and put them in a list of sets.
    frozen_extensions = get_argumentation_framework_extensions(arg_framework, semantics)
    #print('frozen_extensions')
    #print(frozen_extensions)
    extensions = [set(frozen_extension) for frozen_extension in frozen_extensions]

    #print('extensions')
    #print(extensions)
    
    #print('sorted(extensions)')
    #print(sorted(extensions))

    # Make a button for each extension.
    extension_buttons = []
    for extension in sorted(extensions):
        out_arguments = {attacked for attacked in arg_framework.arguments
                         if any(argument in arg_framework.get_incoming_defeat_arguments(attacked)
                                for argument in extension)}
        undecided_arguments = {argument for argument in arg_framework.arguments
                               if argument not in extension and argument not in out_arguments}
        extension_readable_str = '{' + ', '.join(argument.name for argument in sorted(extension)) + '}'
        extension_in_str = '+'.join(argument.name for argument in sorted(extension))
        extension_out_str = '+'.join(argument.name for argument in sorted(out_arguments))
        extension_undecided_str = '+'.join(argument.name for argument in sorted(undecided_arguments))
        extension_long_str = '|'.join([extension_in_str, extension_undecided_str, extension_out_str])
        extension_buttons.append(dbc.Button([extension_readable_str], color='secondary',
                                            id={'type': 'extension-button-abstract', 'index': extension_long_str}))

    # Based on the extensions, get the acceptance status of arguments.
    accepted_arguments = get_accepted_arguments(extensions, strategy)

    # Make a button for each accepted argument.
    accepted_argument_buttons = [dbc.Button(argument.name, color='secondary', id={'type': 'argument-button-abstract',
                                                                                  'index': argument.name})
                                 for argument in sorted(accepted_arguments)]

    return html.Div([#html.B('The extension(s):'), html.Div(extension_buttons),
                     #html.B('The accepted argument(s):'), html.Div(accepted_argument_buttons),
                     html.P('Click on the extension/argument buttons to display the corresponding argument(s) '
                            'in the graph.')])


@callback(
    Output('selected-argument-store-abstract', 'data'),
    Input({'type': 'extension-button-abstract', 'index': ALL}, 'n_clicks'),
    Input({'type': 'argument-button-abstract', 'index': ALL}, 'n_clicks'),
    State('selected-argument-store-abstract', 'data'),
)
def mark_extension_or_argument_in_graph(_nr_of_clicks_extension_values, _nr_of_clicks_argument_values,
                                        old_selected_data: List[str]):
    button_clicked_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    if button_clicked_id == '':
        return old_selected_data
    button_clicked_id_content = json.loads(button_clicked_id)
    button_clicked_id_type = button_clicked_id_content['type']
    button_clicked_id_index = button_clicked_id_content['index']
    if button_clicked_id_type == 'extension-button-abstract':
        in_part, undecided_part, out_part = button_clicked_id_index.split('|', 3)
        return {'green': in_part.split('+'), 'yellow': undecided_part.split('+'), 'red': out_part.split('+')}
    elif button_clicked_id_type == 'argument-button-abstract':
        return {'blue': [button_clicked_id_index]}
    return []


@callback(
    Output('abstract-explanation-function', 'options'),
    Output('abstract-explanation-function', 'value'),
    [Input('abstract-explanation-type', 'value')]
)
def setting_choice(choice: str):
    return EXPLANATION_FUNCTION_OPTIONS[choice], EXPLANATION_FUNCTION_OPTIONS[choice][0]['value']


@callback(
    Output('abstract-explanation', 'children'),
    Input('abstract-evaluation-accordion', 'active_item'),
    State('abstract-arguments', 'value'),
    State('abstract-attacks', 'value'),
    State('abstract-evaluation-semantics', 'value'),
    Input('abstract-explanation-function', 'value'),
    Input('abstract-explanation-type', 'value'),
    State('abstract-evaluation-strategy', 'value'),
    prevent_initial_call=True
)
def derive_explanations_abstract_argumentation_framework(active_item,
                                                         arguments: str, attacks: str,
                                                         semantics: str, explanation_function: str,
                                                         explanation_type: str, explanation_strategy: str):
    if active_item != 'Explanation':
        raise PreventUpdate

    # Compute the explanations based on the input.
    arg_framework = read_argumentation_framework(arguments, attacks)
    frozen_extensions = get_argumentation_framework_extensions(arg_framework, semantics)
    extensions = [set(frozen_extension) for frozen_extension in frozen_extensions]
    accepted_arguments = get_accepted_arguments(extensions, explanation_strategy)
    explanations = get_argumentation_framework_explanations(arg_framework, extensions, accepted_arguments,
                                                            explanation_function, explanation_type)

    # Print the explanations for each of the arguments.
    return html.Div([html.Div(html.B('Explanation(s) by argument:'))] +
                    [html.Div([
                        html.B(explanation_key),
                        html.Ul([html.Li(str(explanation_value).replace('set()', '{}'))
                                 for explanation_value in explanation_values])])
                     for explanation_key, explanation_values in explanations.items()])