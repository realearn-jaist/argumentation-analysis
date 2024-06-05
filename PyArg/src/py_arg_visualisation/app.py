from dash import Dash, html
import dash_bootstrap_components as dbc
import dash
import dash_daq as daq


# Create a Dash app using an external stylesheet.
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.YETI])

# Specification of the layout, consisting of a navigation bar and the page container.
app.layout = html.Div([html.Header([
        html.H1('Internship JAIST 2024'),
        html.H2('Multimodal Argument Mining Dataset for Political Debates with Audio and Transcripts'),
        html.Nav([
            html.Ul([
                html.Li(html.A('Presentation', href='/', id='presentation-link')),
                html.Li(html.A('Visualisation', href='21-visualise-abstract', id='visualisation-link')),
                html.Li(html.A('Contact', href='#', id='contact-link')),
                html.Li(dbc.DropdownMenuItem('Colorblind mode', className='fw-bold text-white')),
                html.Li(daq.BooleanSwitch(id='color-blind-mode', on=False, className='mt-2'))
            ])
        ])
    ]), dbc.Col(html.Div([dash.page_container]), width={'size': 10, 'offset': 1}),
    html.Footer([
        html.P('©CHAVIGNY-Robin. 2024 JAIST Internship.'),
        html.P('Internship supervised by RACHARAK Teeradaj (JAIST) and GUITTON Alexandre (ISIMA).'),
        html.P('Contact: robin.chavigny@etu.uca.fr'),
        html.P(['LinkedIn : ',
            html.A('Robin Chavigny', href='https://www.linkedin.com/in/robin-chavigny-568556292/',target="_blank")
        ])
    ], className='footer')
])

# Running the app.
if __name__ == '__main__':
    app.run_server(debug=False)