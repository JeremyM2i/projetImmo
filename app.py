import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import requests
import unidecode
import json
import ast 
#from plot_scatter import graphe_scatter
import plotly.graph_objects as go
import time
import pickle

######################################################################
######################################################################
#####
#####             import des fichiers pythons externes             
#####
######################################################################
######################################################################

#chargement des données de départements
#shapes
pd.options.mode.chained_assignment = None 
Time0=time.time()
print("\n------------\nchargement des départements")
repo_url_dep = "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"
france_dep = requests.get(repo_url_dep).json()
for i,val in enumerate(france_dep['features']):
    modif=unidecode.unidecode(france_dep['features'][i]['properties']['nom'].lower())
    france_dep['features'][i]['properties']['nom']=modif
#données immmo aggrégées
df_dep=pd.read_parquet("data_par_dept.parquet.gzip")
df_dep=df_dep.loc[df_dep.Annee=="0"]
df_dep=df_dep.reset_index(drop=True)
df_dep["Nom Dept"]=pd.Series([x.lower() for x in df_dep["Nom Dept"]])
Time1=cTime=time.time()
print("départements chargés en",round(Time1-Time0,1),"secondes, chargement des régions")

#chargement des données de régions
#shapes
repo_url_reg = "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
france_reg = requests.get(repo_url_reg).json()
for i,val in enumerate(france_reg['features']):
    modif=unidecode.unidecode(france_reg['features'][i]['properties']['nom'].lower())
    france_reg['features'][i]['properties']['nom']=modif
#données immmo aggrégées
df_reg=pd.read_parquet("data_par_region.parquet.gzip")
df_reg=df_reg.loc[df_reg.Annee=="0"]
df_reg=df_reg.reset_index(drop=True)
df_reg["Nom Reg"]=pd.Series([x.lower() for x in df_reg["Nom Reg"]])
df_reg["Nom Reg"][0]="grand est"
df_reg["Nom Reg"][1]="nouvelle-aquitaine"
df_reg["Nom Reg"][13]="hauts-de-france"
df_reg["Nom Reg"][11]="occitanie"
Time2=cTime=time.time()
print("régions chargées en",round(Time2-Time1,1),"secondes chargement des shapes de communes")

#chargement des données de communes
#shapes
with open('communes-20190101.pkl', 'rb') as f1:
    france_com=pickle.load(f1)

#données immmo aggrégées
Time3=cTime=time.time()
print("shape des communes chargées en",round(Time3-Time2,1),"secondes chargement des données aggrégées de communes")

df_communes=pd.read_parquet("data_par_commune.parquet.gzip")
df=df_communes.copy()
df_communes=df_communes.loc[df_communes.Annee=="0"]
Time4=cTime=time.time()
print("communes chargées en",round(Time4-Time3,1),"secondes création du graphique")



app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
#server = app.server


app.layout = html.Div(
    #print(df)


    [
        dcc.Tabs([
            dcc.Tab(label="Overview géographique", children=[ 
                dcc.Dropdown(
                        id='dropdown_choro_metrique',
                        options=[
                            {'label': "Valeur foncière", 'value': 'Valeur_fonciere'},
                            {'label': 'Prix au m²', 'value': 'Prix_m2'},
                            {'label': 'Prix surface au sol au m²', 'value': 'Prix_m2_b'},
                            {'label': 'Prix surface terrain au m²', 'value': 'Prix_m2_s1'}
                        ],
                        value='Valeur_fonciere'
                    ),
                dcc.Dropdown(
                        id='dropdown_choro_geo',
                        options=[
                            {'label': "Région", 'value': 'Reg'},
                            {'label': 'Départements', 'value': 'Dep'},
                            {'label': 'Communes (choisissez un département) patienter', 'value': 'Com'},
                        ],
                        value='Dep'
                    ),
                dcc.Dropdown(
                        id='dropdown_choro_choixDep',
                        options=[
                                {'label': 'Seine-Maritime' , 'value': "SEINE-MARITIME"},
                                {'label': 'Hérault' , 'value': "HERAULT"},
                                {'label': "Manche", 'value': "MANCHE"}
                        ],
                        value='SEINE-MARITIME'
                    ),
                dcc.Graph(id='choro')#,figure=fig_choro
#

            ]),
            dcc.Tab(label="Évolution temporelle", children=[
                html.I("Saisir du text"),
                html.Br(),
                dcc.Input(id="code_insee", type="text", value="01001"),
                html.Button('Estimer le prix', id='button_run', n_clicks=0),
                dcc.Dropdown(
                        id='dropdown_type_surface',
                        options=[
                            {'label': "Valeur foncière", 'value': 'Valeur_fonciere'},
                            {'label': 'Prix au m²', 'value': 'Prix_m2'},
                            {'label': 'Prix surface au sol au m²', 'value': 'Prix_m2_b'},
                            {'label': 'Prix surface terrain au m²', 'value': 'Prix_m2_s1'}
                        ],
                        value='Valeur_fonciere'
                    ),
                dcc.Graph(id='scatter'),
                dcc.Graph(id='scatter2')
            ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),




            dcc.Tab(label="Prédiction/Estimation", children=[

            ]),
            dcc.Tab(label="Informations", children=[


            ])
        ])
    ]
)




######################################################################
######################################################################
#####
#####             Création des graphiques             
#####
######################################################################
######################################################################

#definition des parametres du graphique choropethe

@app.callback(
    dash.dependencies.Output('choro', 'figure'),
    dash.dependencies.Input('dropdown_choro_metrique', "value"),
    dash.dependencies.Input('dropdown_choro_geo', "value"),
    dash.dependencies.Input('dropdown_choro_choixDep', "value"),
    state=[dash.dependencies.State('dropdown_choro_metrique', 'value'),
            dash.dependencies.State('dropdown_choro_geo', 'value'),
             dash.dependencies.State('dropdown_choro_choixDep', 'value')
           ])
def dessinerchoro(a,x,z,regarder,choix,pourCommunes):
    #regarder='Valeur_fonciere'#Prix_m2 	Prix_m2_b 	Prix_m2_s1
    #choix="Dep"
    if choix =="Dep":
        df=df_dep
        shape=france_dep
        cle='properties.nom'
        colonne='Nom Dept'
    elif choix == "Reg":
        df=df_reg
        shape=france_reg
        cle='properties.nom'
        colonne='Nom Reg'
    elif choix=="Com":
        df=df_communes
        df=df[df["Nom Dept"]==pourCommunes]
        shape=france_com
        cle='properties.insee'
        colonne='Code_Insee'
        regarder='Valeur_fonciere'#Prix_m2 	Prix_m2_b 	Prix_m2_s1
    maximum=max(df[regarder])
    if regarder=="Valeur_fonciere":
        minimum=10000
        maximum=300000
    elif regarder=="Prix_m2":
        minimum=0
        maximum=700
    elif regarder=="Prix_m2_b":
        minimum=0
        maximum=3000
    elif regarder=="Prix_m2_s1":
        minimum=0
        maximum=700
    #Carte choroplethe

    fig_choro= px.choropleth(data_frame=df, 
                        geojson=shape,#france_geo, 
                        locations=colonne, # name of dataframe column
                        featureidkey=cle,  # path to field in GeoJSON feature object with which to match the values passed in to locations
                        color=regarder,
                        color_continuous_scale="Bluered",
                        scope="europe",
                        range_color=[minimum,maximum],
                    )
    fig_choro.update_geos(showcountries=False, showcoastlines=False, showland=False, fitbounds="locations")
    fig_choro.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return(fig_choro)

#df est cree plus haut
df["Annee"]=pd.to_numeric(df["Annee"],downcast="integer")
df["Departement"]=df.Code_Insee.apply(lambda x : x[0:2])
#print(df)

@app.callback(
    dash.dependencies.Output('scatter', 'figure'),
    dash.dependencies.Output('scatter2', 'figure'),
    dash.dependencies.Input('button_run', "n_clicks"),
    dash.dependencies.Input('dropdown_type_surface', "value"),
 
    state=[dash.dependencies.State('code_insee', 'value'),
            dash.dependencies.State('dropdown_type_surface', 'value')
           ])
def update_output(n_click,dropdown_type_surface,code_insee,type_surf):
    global df
    if type_surf=="Valeur_fonciere": nameAxis="Valeur foncière médiane"
    if type_surf=="Prix_m2": nameAxis="Prix m² médian"
    if type_surf=="Prix_m2_b": nameAxis="Prix m² médian de la surface au sol"
    if type_surf=="Prix_m2_s1": nameAxis="Prix m² médian de la surface terrain"
 
    customdata=df[df.Code_Insee==code_insee]
    customdata=customdata[customdata.Annee!=0]
    fig=px.line(customdata, x="Annee", y=type_surf,
        labels={
                     "Annee": "Année",
                     type_surf: nameAxis
                 })
    fig.update_xaxes(tickangle=45,
                 tickmode = 'array',
                 tickvals = customdata["Annee"])
    fig.update_traces(mode='markers+lines')
    customdata2=df[df.Departement==code_insee[0:2]]
    customdata2=customdata2[customdata2.Annee==0]
    customdata2["color_code"]="Autre Commune du département"
    customdata2.loc[(customdata2.Code_Insee==code_insee),'color_code']=customdata2[customdata2.Code_Insee==code_insee]["Code_Insee"]
    customdata2["color_code"]=customdata2["color_code"].astype("str")
    fig2 = px.scatter(customdata2, x="Code_Insee", y=type_surf,
                size='densitePop',
                color="color_code",
                labels={
                     #"Code_Insee": "Code Insee",
                     type_surf: nameAxis,
                     "densitePop":"Densité de population"
                 },
                hover_data =["Prix_m2"],
                title="Zob")
    return(fig,fig2)


if __name__ == '__main__':
    app.run_server(debug=True)