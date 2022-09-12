#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 10 17:27:05 2022

@author: louisteillets
"""
#%% Import des modules 

import streamlit as st 
from streamlit_option_menu import option_menu
import datetime as dt
# Using plotly.express
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib import style
import pandas as pd
import pandas_datareader.data as web
import glob
import os


#%%
#Titre du site
st.title("Portfolio Dashboard")

# Menu déroulant 
with st.sidebar:
    choose=option_menu("Menu", ["Portfolio Dashboard", "Deposit/Stock modification"],
                                 icons=['graph-up-arrow', 'bank'],
                                 menu_icon="app-indicator", default_index=0,
                                 styles={
                "container": {"padding": "5!important", "background-color": "#FFFFFF"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#020C43"},})
    

#%%


# # Montant total déposé en euros
# depot_total_eu=850.00
# # Montant équivalent en dollar suivant le taux change à chaque dépot
# depot_total_us = 876.95
# # Valeur actuelle totale sur le compte en dollar
# current_value = 830.89

# # Positions mises 

# #Ticker actuellement dans le portfefeuille
# portfolio_ticker = ["ASML","FEZ","ORAN"]

# portfolio=pd.DataFrame({"Net Investi":[100,-50,41.20],
#                              "Date ouverture":[dt.datetime(2022,8,30),
#                                                dt.datetime(2022,9,9),
#                                                dt.datetime(2022,8,15)],
#                              "Prix ouverture":[506.9299,34.4789,10.30],
#                              "Unité":[0.09863,1.45016,4.00]},
#                             index=portfolio_ticker)


start = dt.datetime(2022,8, 15)
end = dt.datetime.now()

st.experimental_memo()
def last_file_metrics():
    list_of_metrics = glob.glob('/Users/louisteillet/Documents/Work/Projet info/Portfolio_site/metrics*.pkl') # * means all if need specific format then *.csv
    latest_metrics = max(list_of_metrics, key=os.path.getctime)
    return latest_metrics
metrics=pd.read_pickle(last_file_metrics())


@st.cache(allow_output_mutation=True)
def import_previous_data():
    #list_of_metrics = glob.glob('/Users/louisteillet/Documents/Work/Projet info/Portfolio Dashboard/metrics*.pkl') # * means all if need specific format then *.csv
    list_of_portfolio = glob.glob('/Users/louisteillet/Documents/Work/Projet info/Portfolio_site/portfolio_info*.pkl') # * means all if need specific format then *.csv
 
    #latest_metrics = max(list_of_metrics, key=os.path.getctime)
    latest_portfolio = max(list_of_portfolio, key=os.path.getctime)
    
    portfolio=pd.read_pickle(latest_portfolio)

    
    return portfolio

portfolio=import_previous_data()

@st.cache()
def import_ticker_data(ticker_list):
    start = dt.datetime(2015,1, 1)
    end = dt.datetime.now()
    list_df ={}
    for ticker in ticker_list:
        df = web.DataReader(ticker, 'yahoo', start, end)
        df.reset_index(inplace=True)
        df.set_index("Date", inplace=True)
        list_df[ticker]=df
    return list_df
        
@st.cache()
def initialisation():
    list_ticker_data = import_ticker_data(portfolio.index)
    
    #ticker_investi = portfolio.dropna().index
    
    portfolio_value = pd.DataFrame(index=list_ticker_data[list(list_ticker_data.keys())[0]].index)
    for ticker in portfolio.index:
        if portfolio.loc[ticker]["Net Investi"]<0:
            portfolio_value[ticker]=-2*portfolio.loc[ticker]["Net Investi"]-list_ticker_data[ticker]["Close"]*portfolio.loc[ticker]["Unité"]
        else:
            portfolio_value[ticker]=list_ticker_data[ticker]["Close"]*portfolio.loc[ticker]["Unité"]
        portfolio_value[ticker]=portfolio_value[portfolio_value.index>=portfolio.loc[ticker]["Date ouverture"]][ticker]
    
    
    
    portfolio_value["Stocks Value"]=portfolio_value[portfolio.index].sum(axis=1)
    portfolio_value=pd.merge(portfolio_value,abs(portfolio.set_index("Date ouverture")["Net Investi"]),left_index=True,right_index=True,how="left")
    portfolio_value["Net Investi"]=portfolio_value["Net Investi"].fillna(0).cumsum()
    portfolio_value["Cash Value"]=metrics["Deposit US"].sum()-portfolio_value["Net Investi"]
    portfolio_value["Total Value"]= round(portfolio_value["Stocks Value"]+portfolio_value["Cash Value"],2)
    portfolio["Current Value"]= round(portfolio_value.iloc[-1]/portfolio["Unité"],2)
    current_total = portfolio_value["Cash Value"].iloc[-1]+portfolio_value["Stocks Value"].iloc[-1]
    
    return portfolio_value,list_ticker_data,current_total


    
portfolio_value,list_ticker_data,current_total=initialisation()

# Savings
@st.cache()
def save():
    print("SAVING")
    today=dt.date.today().strftime("%d_%m_%Y")
    portfolio.to_pickle("/Users/louisteillet/Documents/Work/Projet info/Portfolio_site/portfolio_"+today+".pkl")
   
save()  

#%%
if choose=="Portfolio Dashboard":
    
    
    col1,col2,col3=st.columns(3)
    col1.metric("Total Deposit (€)",metrics["Deposit EU"].sum())
    col2.metric("Total Deposit ($)",metrics["Deposit US"].sum())
    col3.metric("Total Current Value ($)",round(current_total,2))
    
    st.header("Total Stocks Value")
    last_date=portfolio_value.index[-1]
    fig = px.line(portfolio_value,y="Stocks Value",range_x=[last_date-pd.DateOffset(months=1),last_date])
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    st.plotly_chart(fig)
    
    st.header("Stocks Value")
    selected_stock=st.selectbox("Selectionnez l'une de vos actions", portfolio.index)
    last_date=list_ticker_data[selected_stock].index[-1]
    fig = px.line(list_ticker_data[selected_stock],y="Close",range_x=[last_date-pd.DateOffset(months=1),last_date])
    if not pd.isnull(portfolio.loc[selected_stock]["Date ouverture"]):
        fig.add_vline(x=portfolio.loc[selected_stock]["Date ouverture"], line_width=3, line_dash="dash", line_color="green")
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    st.plotly_chart(fig)
    
    st.header("Cash Value")
    last_date=portfolio_value.index[-1]

    fig = px.line(portfolio_value,y="Cash Value",range_x=[last_date-pd.DateOffset(months=1),last_date])
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(step="all"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward")
            ])
        )
    )
    st.plotly_chart(fig)
    
    st.header("Portfolio Composition")
    st.table(portfolio.dropna().sort_values(by="Date ouverture"))
    

    
    #/Users/louisteillet/Documents/Work/Projet info/Portfolio Dashboard/portfolio_dashboard.py
    
    

elif choose=="Deposit/Stock modification":
    
    deposit,stocks=st.tabs(["💰 Deposit","🛒 Stocks update"])
    with deposit:
        today=dt.date.today().strftime("%d_%m_%Y")
        clear_btn=st.button("Clear the dataframe")
        if clear_btn:
            metrics=metrics[0:0]
            metrics.to_pickle("/Users/louisteillet/Documents/Work/Projet info/Portfolio Dashboard/metrics_"+today+".pkl")    
            st.success('The dataframe has been cleared', icon="✅")
        with st.form("my_form"):
            deposit_eu = st.number_input("How much do you want to depose in €?")
            deposit_us = st.number_input("How much do you want to depose in $?")
            deposit_date = st.date_input("When was the deposit ? ")
             # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.write(f"{deposit_eu}€ has been added.", f" It corresponds to {deposit_us}$")
                metrics.loc[deposit_date]=[deposit_eu,deposit_us]
                
                
                metrics[["Deposit EU","Deposit US"]].to_pickle("/Users/louisteillet/Documents/Work/Projet info/Portfolio Dashboard/metrics_"+today+".pkl")    
    
        
    
        metrics_plot=metrics.copy(deep=True)
        metrics_plot.sort_index(inplace=True)
        metrics_plot["Total EU"]=metrics_plot["Deposit EU"].cumsum()
        metrics_plot["Total US"]=metrics_plot["Deposit US"].cumsum()
        
            
            
        st.table(metrics_plot)
    
    
    

    
    

  
    
    
    
    
    
    
    