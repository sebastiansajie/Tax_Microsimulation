# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 18:28:24 2021

@author: wb305167
"""

import copy
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import *
import tkinter.font as tkfont
from datetime import datetime

#from taxcalc import *
from taxcalc.utils import *
from taxcalc.display_funcs import *
from PIL import Image,ImageTk


def make_float(item):
    if isinstance(item, list):
        return [float(x) for x in item]
    else:
        return float(item)
    
def read_reform_dict(block_selected_dict):
    print('block_selected_dict in read_reform_dict: ',block_selected_dict)
    years=[]
    for k in block_selected_dict.keys():
        if (block_selected_dict[k]['selected_year'] not in years):
            years = years + [block_selected_dict[k]['selected_year']]
    ref = {}
    ref['policy']={}
    for year in years:
        policy_dict = {}
        for k in block_selected_dict.keys():
            if block_selected_dict[k]['selected_year']==year:
                policy_dict['_'+block_selected_dict[k]['selected_item']]=[make_float(block_selected_dict[k]['selected_value'])]
        ref['policy'][int(year)] = policy_dict
    years.sort()
    years = [int(x) for x in years]
    return years, ref

def concat_dicts(block_selected_dict, elasticity_dict):
    years=[]
    max = 0
    for k in block_selected_dict.keys():
        if int(k) > max:
            max = int(k)
    for i in range(1,len(elasticity_dict)+1):
        block_selected_dict[str(max+i)] = elasticity_dict[str(i)]
    #ref = {}
    return block_selected_dict

def fact():
    print("12345")
    f = open('reform.json')
    vars = json.load(f)
    print("block_selected_dict from json",vars)
    print("54321")

def write_file(df, text_data, filename, window, footer_row_num):
    df.to_csv(filename+'.csv', mode='w')
    # a = open(filename+'.csv','w')
    # a.write("\n")
    # a.write("\n")
    # a.close
    with open(filename+'.txt','w') as f:
        f.write(text_data)
    f.close
    footer = ["footer", "*Data saved in file "+ filename]
    display_table(window, data=footer, footer=footer_row_num+2)

def weighted_total_tax(calc, tax_list, category, year, tax_dict):
    for tax_type in tax_list:
        tax_dict[tax_type][year][category] = {}
        if tax_type == 'pit':
            tax_dict[tax_type][year][category]['value'] = calc.weighted_total_pit(tax_type+'ax')       
        if tax_type == 'cit':
            tax_dict[tax_type][year][category]['value'] = calc.weighted_total_cit(tax_type+'ax')           
        if tax_type == 'vat':
            tax_dict[tax_type][year][category]['value'] = calc.weighted_total_gst(tax_type+'ax')

        tax_dict[tax_type][year][category]['value_bill'] =  tax_dict[tax_type][year][category]['value']/10**9
        tax_dict[tax_type][year][category]['value_bill_str'] =  '{0:.2f}'.format(tax_dict[tax_type][year][category]['value_bill'])        
    return tax_dict
       
def weighted_total_tax_diff(tax_list, category1, category2, year, tax_dict):
    for tax_type in tax_list:
        tax_dict[tax_type][year][category2]['value_bill_diff'] = (tax_dict[tax_type][year][category2]['value_bill'] -
                                                                  tax_dict[tax_type][year][category1]['value_bill'])
        tax_dict[tax_type][year][category2]['value_bill_diff_str'] = '{0:.2f}'.format(tax_dict[tax_type][year][category2]['value_bill_diff'])
    return tax_dict

def screen_print(tax_list, category, year, tax_dict, item, item_desc):
    for tax_type in tax_list:
        print("The "+tax_type.upper()+" "+item_desc+" in billions is: ", tax_dict[tax_type][year][category][item])

    
def generate_policy_revenues():
    from taxcalc.growfactors import GrowFactors
    from taxcalc.policy import Policy
    from taxcalc.records import Records
    from taxcalc.gstrecords import GSTRecords
    from taxcalc.corprecords import CorpRecords
    from taxcalc.parameters import ParametersBase
    from taxcalc.calculator import Calculator
    
    """
    for num in range(1, num_reforms):
        block_selected_dict[num]['selected_item']= block_widget_dict[num][1].get()
        block_selected_dict[num]['selected_value']= block_widget_dict[num][3].get()
        block_selected_dict[num]['selected_year']= block_widget_dict[num][2].get()
    print(block_selected_dict)
    """

    

    f = open('global_vars.json')
    vars = json.load(f)
    
    #income_measure = vars['income_measure']
    start_year = vars['start_year']
    end_year = vars['end_year']
    
    tax_list=[]
    tax_collection_var_list = []    
    # start the simulation for pit/cit/vat    
    if vars['pit']:
        tax_list = tax_list + ['pit']
        tax_collection_var_list = tax_collection_var_list + ['pitax']
        recs = Records(data=vars['pit_data_filename'], weights=vars['pit_weights_filename'], gfactors=GrowFactors(growfactors_filename=vars['GROWFACTORS_FILENAME']))
        elasticity_filename = vars['pit_elasticity_filename']
    else:
        recs = None
    if vars['cit']:
        tax_list = tax_list + ['cit']
        tax_collection_var_list = tax_collection_var_list + ['citax']
        crecs = CorpRecords(data=vars['cit_data_filename'], weights=vars['cit_weights_filename'], gfactors=GrowFactors(growfactors_filename=vars['GROWFACTORS_FILENAME']))
        elasticity_filename = vars['cit_elasticity_filename']
    else:
        crecs = None
    if vars['vat']:
        tax_list = tax_list + ['vat']
        tax_collection_var_list = tax_collection_var_list + ['vatax']
        grecs = GSTRecords(data=vars['vat_data_filename'], weights=vars['vat_weights_filename'], gfactors=GrowFactors(growfactors_filename=vars['GROWFACTORS_FILENAME']))
        elasticity_filename = vars['vat_elasticity_filename']
    else:
        grecs = None  
    
    adjust_behavior = 0
    for tax_type in tax_list:
        adjust_behavior = adjust_behavior or vars[tax_type+'_adjust_behavior']
    
    f = open('reform.json')
    block_selected_dict = json.load(f)
    print("block_selected_dict from json",block_selected_dict)
    
    # create Policy object containing current-law policy
    pol = Policy(DEFAULTS_FILENAME=vars['DEFAULTS_FILENAME'])
    
    # specify Calculator objects for current-law policy
    calc1 = Calculator(policy=pol, records=recs, corprecords=crecs, gstrecords=grecs, verbose=False)    
    assert isinstance(calc1, Calculator)
    assert calc1.current_year == vars["start_year"]
    np.seterr(divide='ignore', invalid='ignore')
    pol2 = Policy(DEFAULTS_FILENAME=vars['DEFAULTS_FILENAME'])      
    years, reform=read_reform_dict(block_selected_dict)
    pol2.implement_reform(reform['policy'])
    calc2 = Calculator(policy=pol2, records=recs, corprecords=crecs, gstrecords=grecs, verbose=False)

    tax_collection_var = tax_collection_var_list[0] 

    if adjust_behavior:    
        elasticity_dict = {}
        for tax_type in tax_list:
            f = open(tax_type+'_elasticity_selection.json')
            elasticity_dict[tax_type] = json.load(f)
            print(elasticity_dict)
            block_selected_dict = concat_dicts(block_selected_dict, elasticity_dict[tax_type])
        print(block_selected_dict)
        pol3 = Policy(DEFAULTS_FILENAME=vars['DEFAULTS_FILENAME'])   
        years, reform=read_reform_dict(block_selected_dict)
        pol3.implement_reform(reform['policy'])
        calc3 = Calculator(policy=pol3, records=recs, corprecords=crecs, gstrecords=grecs, verbose=False)
      
    #print("block_selected_dict after merging: ", block_selected_dict)       
    total_revenue_text={}
    reform_revenue_text={}
    revenue_dict={}
    revenue_amount_dict = {}
    num = 1
    first_time = True
    i=1
    j=0
    #rows = []
    
    window_dict={}
    row_num = {}
    data_row = {}
    for tax_type in tax_list:
        revenue_dict[tax_type]={}
        for year in range(start_year, end_year):
            revenue_dict[tax_type][year]={}
        window_dict[tax_type] = tk.Toplevel()
        window_dict[tax_type].geometry("800x600+140+140")
        #display_table(window, header=True)
        # Adjust this for number of years selected
        header = ["header","Year", "Current Law", "Reform", "Diff"]
        if vars[tax_type+'_adjust_behavior']:
            header = header + ['Reform (Behavior)', "Diff"]
        title_header = [["title", tax_type.upper()+" Projections"],
                        header]            
        row_num[tax_type] = display_table(window_dict[tax_type], data=title_header, header=True)


    for year in range(start_year, end_year):
        
        calc1.advance_to_year(year)
        calc2.advance_to_year(year)
        calc1.calc_all()
        calc2.calc_all()
        
        revenue_dict = weighted_total_tax(calc1, tax_list, 'current_law', year, revenue_dict)              
        print(f'TAX COLLECTION FOR THE YEAR - {year} \n')        
        screen_print(tax_list, 'current_law', year, revenue_dict, 'value_bill', 'Collection')
       
        revenue_dict = weighted_total_tax(calc2, tax_list, 'reform', year, revenue_dict)
        print(f'\nTAX COLLECTION FOR THE YEAR UNDER REFORM - {year} \n')       
        screen_print(tax_list, 'reform', year, revenue_dict, 'value_bill', 'Collection')
        
        revenue_dict = weighted_total_tax_diff(tax_list, 'current_law', 'reform', year, revenue_dict)
        screen_print(tax_list, 'reform', year, revenue_dict, 'value_bill_diff', 'Collection difference under Reform')

        for tax_type in tax_list:        
            data_row[tax_type] = [str(year), revenue_dict[tax_type][year]['current_law']['value_bill_str'], 
                                  revenue_dict[tax_type][year]['reform']['value_bill_str'], 
                                  revenue_dict[tax_type][year]['reform']['value_bill_diff_str']]       
        if adjust_behavior:
        #redo the calculations by including behavioral adjustment
            calc3.advance_to_year(year)
            calc3.calc_all()
            revenue_dict = weighted_total_tax(calc3, tax_list, 'reform_behavior', year, revenue_dict)
            print(f'\nTAX COLLECTION FOR THE YEAR UNDER REFORM WITH BEHAVIOR ADJUSTMENT - {year} \n')
            screen_print(tax_list, 'reform_behavior', year, revenue_dict, 
                         'value_bill', 'Collection with Behavioral Adjustment')
            revenue_dict = weighted_total_tax_diff(tax_list, 'current_law', 'reform_behavior', year, revenue_dict)
            screen_print(tax_list, 'reform_behavior', year, revenue_dict, 
                         'value_bill_diff',
                         'Collection difference with Behavioral Adjustment')
            for tax_type in tax_list:            
                data_row[tax_type] = data_row[tax_type] + [revenue_dict[tax_type][year]['reform_behavior']['value_bill_str'], 
                                                           revenue_dict[tax_type][year]['reform_behavior']['value_bill_diff_str']]
        for tax_type in tax_list:         
            row_num[tax_type] = display_table(window_dict[tax_type], 
                                              data = data_row[tax_type], 
                                              row = row_num[tax_type])
        #display_table(window, revenue_dict_pit=revenue_dict_pit, year=year, row=i)
        i=i+1
        tax_type='pit'
        if vars[tax_type+'_distribution_table']:
            output_in_averages = True
            #output_categories = 'standard_income_bins'
            output_categories = 'weighted_deciles'
            # pd.options.display.float_format = '{:,.3f}'.format
            # dt1, dt2 = calc1.distribution_tables(calc2, 'weighted_deciles')
            dt1, dt2 = calc1.distribution_tables(calc2, output_categories, income_measure=income_measure,
                                                 averages=output_in_averages,
                                                 scaling=True)
            dt1 = dt1.rename(columns={tax_collection_var:tax_collection_var+'_'+str(year)})
            dt2 = dt2.rename(columns={tax_collection_var:tax_collection_var+'_ref_'+str(year)})
            #deciles_list = ['0-10p','10-20','20-30','30-40','40-50','50-60', '60-70','70-80','80-90','90-100']
            print(dt2)
            if first_time:
                dt=dt1[[tax_collection_var+'_'+str(year)]].join(dt2[[tax_collection_var+'_ref_'+str(year)]])
                first_time=False
            else:
                dt=dt.join(dt2[[tax_collection_var+'_ref_'+str(year)]])
    #save the results
    now = datetime.now() # current date and time
    date_time = now.strftime("%d_%m_%Y_%H_%M_%S")
    df = {}
    for tax_type in tax_list:
        #filename1 = 'Revenue Data_'+'_'+tax_type+'_'+date_time
        filename_chart_rev_projection = 'revenue_projections'
        with open('revenue_dict.json', 'w') as f:
            json.dump(revenue_dict, f)
        revenue_dict_df = {}
        for k, v in revenue_dict[tax_type].items():
            revenue_dict_df[k] = {}
            revenue_dict_df[k]['current_law'] = revenue_dict[tax_type][k]['current_law']['value_bill_str']
            revenue_dict_df[k]['reform'] = revenue_dict[tax_type][k]['reform']['value_bill_str']
            if adjust_behavior:
                revenue_dict_df[k]['reform_behavior'] = revenue_dict[tax_type][k]['reform_behavior']['value_bill_str']
        df[tax_type] = pd.DataFrame.from_dict(revenue_dict_df)   
        df_str = df[tax_type].to_string()
        df_reform = pd.DataFrame.from_dict(reform)
        df_reform_str = df_reform.to_string()
        text_output1 = df_str + '\n\n' + df_reform_str + '\n\n'
        l = tk.Button(window_dict[tax_type],text="Save Results",command=lambda: write_file(df[tax_type], text_output1, filename_chart_rev_projection, window_dict[tax_type], row_num[tax_type]))
        l.grid(row=row_num[tax_type]+2, column=2, pady = 10, sticky=tk.W)
    #footer = ["footer", "*Data saved in file "+ filename1]
    #row_num = display_table(window, data=footer, footer=row_num+2)
    """    
    if vars[tax_type+'_distribution_table']:
        window_dist = tk.Toplevel()
        window_dist.geometry("800x700+200+200")
        dt.update(dt.select_dtypes(include=np.number).applymap('{:,.0f}'.format))
        dt.to_pickle('file.pkl')
        dt = pd.read_pickle('file.pkl')
        #dt = dt.reset_index()
        # Adjust this for number of years selected
        header1 = ["header","", tax_type.upper()]
        header2 = ["header",'Decile','Current Law '+str(start_year)]
        for year in range(start_year, end_year):
            header1 = header1+[tax_type.upper()]
            header2 = header2+['Reform '+str(year)]          
        title_header = [["title", tax_type.upper()+" Distribution"],
                        header1, header2]      
        footer = ["footer", "*Data saved in file datadump.csv"]         
        row_num = display_table(window_dist, data=title_header, header=True)   
        row_num = display_table(window_dist, row = row_num, dataframe=dt)       
        
        now = datetime.now() # current date and time
        date_time = now.strftime("%d_%m_%Y_%H_%M_%S")
        filename2 = 'Distribution Data_'+date_time
        text_output2 = dt.to_string() + '\n\n'
        l = tk.Button(window_dist,text="Save Results",command=lambda: write_file(dt, text_output2, filename1, window_dist, row_num))
        l.grid(row=row_num+2, column=2, pady = 10, sticky=tk.W)
        #footer = ["footer", "*Data saved in file "+ filename1]
        #row_num = display_table(window_dist, data=footer, footer=row_num+2)
     """   
    
    #pt = Table(f, dataframe=dt,
       #showtoolbar=True, showstatusbar=True)
        
"""    
    #redo the calculations by including behavioral adjustment
    recs = Records(data=vars['pit_data_filename'], weights=vars['pit_weights_filename'], gfactors=GrowFactors(growfactors_filename=vars['GROWFACTORS_FILENAME']))
    pol2 = Policy(DEFAULTS_FILENAME=vars['DEFAULTS_FILENAME'])   
    years, reform=read_reform_dict(block_selected_dict)
    #print("reform dictionary: ",reform) 
    pol2.implement_reform(reform['policy'])
    calc2 = Calculator(policy=pol2, records=recs, verbose=False)
    assert isinstance(calc2, Calculator)
    assert calc2.current_year == 2017
    np.seterr(divide='ignore', invalid='ignore')

    for year in range(2019, 2023):
        calc2.advance_to_year(year)
        calc2.adjust_behavior(first_year=2019)
        calc2.calc_all()
        
        weighted_pitax3 = calc2.weighted_total_pit('pitax')                
        pitax_collection_billions3 = weighted_pitax3/10**9        
        pitax_collection_str3 = '{0:.2f}'.format(pitax_collection_billions3)
        
        print('\n\n\n')
        print(f'TAX COLLECTION FOR THE YEAR UNDER REFORM WITH BEHAVIOR ADJUSTMENT - {year} \n')   
        print("The PIT Collection in billions is: ", pitax_collection_billions3)

        pitax_diff_collection_billions4 = (pitax_collection_billions3-pitax_collection_billions1)        
        pitax_diff_collection_str4 = '{0:.2f}'.format(pitax_diff_collection_billions4)
                          
        #save the results
        
        revenue_dict_pit[year]['reform_behavior']=pitax_collection_str3
        revenue_dict_pit[year]['reform_behavior_difference']=pitax_diff_collection_str4
        
        display_table(window, revenue_dict_pit=revenue_dict_pit, year=year, row=i)
        i=i+1

   
    display_table(window, footer=i)
"""
    
"""
    #print(revenue_amount_dict)
    df_revenue_proj = pd.DataFrame(revenue_amount_dict)
    df_revenue_proj = df_revenue_proj.T
    df_revenue_proj['Current Law'] = df_revenue_proj['current_law'].apply(pd.Series)
    df_revenue_proj['Reform'] = df_revenue_proj['reform'].apply(pd.Series)
    df_revenue_proj = df_revenue_proj.drop(['current_law', 'reform'], axis=1)
    df_revenue_proj['Current Law'] = pd.to_numeric(df_revenue_proj['Current Law'])
    df_revenue_proj['Reform'] = pd.to_numeric(df_revenue_proj['Reform'])
    print("Revenues\n", df_revenue_proj)
    ax = df_revenue_proj.plot(y=["Current Law", "Reform"], kind="bar", rot=0,
                        figsize=(8,8))
    ax.set_ylabel('(billion )')
    ax.set_xlabel('')
    ax.set_title('CIT Revenue - Current Law vs. Reforms', fontweight="bold")
    pic_filename2 = 'PIT - Current Law and Reforms.png'
    
    plt.savefig(pic_filename2)
    
    img1 = Image.open(pic_filename2)
    img2 = img1.resize((500, 500), Image.ANTIALIAS)
    img3 = ImageTk.PhotoImage(img2)
    pic.configure(image=img3)
    pic.image = img3
"""
       
    
