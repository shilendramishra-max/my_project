#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 13:26:26 2021
nsdl_aeps with envs

@author: shilendra.mishra
"""
import numpy as np
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
from datetime import date as d
import os
from google.oauth2 import service_account
from google.cloud import storage
from datetime import timedelta




# key_path='/home/sdlreco/crons/nsdl_aeps/spicemoney-dwh-aman-key.json'

def main(nsdl_aeps,i):

    current_date = d.today()-timedelta(i+1) # any number replace with 1

    date = d.today()-timedelta(i)
    current_year = date.strftime('%Y')  #yes
    
    date = d.today()-timedelta(i+1)
    current_year2 = date.strftime('%Y')  #yes

    date = date.today()-timedelta(i)
    current_month = date.strftime('%m')   # yes
    
    date = date.today()-timedelta(i) # testing then remove timedelta
    current_day = date.strftime('%d')     #yes

    date2 = d.today()-timedelta(i+1) # any number replace with 1  
    current_day9 = date2.strftime('%d')  #yes
    
    date2 = d.today()-timedelta(i+1) # constant 1
    current_month_name = date2.strftime("%^b")    #yes %b=Aug %B=August   %^b=AUG %^B=AUGUST
    
    date2 = d.today()-timedelta(i+1) # constant 1
    current_month_name2 = date2.strftime("%b")          
        
    # credentials = service_account.Credentials.from_service_account_file(key_path)
    project_id = 'spicemoney-dwh'
    client = bigquery.Client(
                             project=project_id, location='asia-south1')
    
    fa=open('/home/sdlreco/crons/nsdl_aeps/error/missing-'+str(dates)+'.txt', 'w')
    fa.close()

    file_path = [str(current_year)+'/'+str(current_month)+'/'+str(current_day)+'/NSDLAEPSTransaction Report/Daily_AEPS_Transaction_'+str(current_day9)+'-'+str(current_month_name)+'-'+str(current_year2)+'-SPICE_MONEY/Daily_AEPS_Transaction-'+str(current_day9)+'-'+str(current_month_name)+'-'+str(current_year2)+'-SPICE_MONEY.txt',str(current_year)+'/'+str(current_month)+'/'+str(current_day)+'/NSDLM2B_AEPSStatement/Account_Statement_'+str(current_day9)+str(current_month_name2)+'_502000053575.xlsx']

    def status(projectname,  bucket_name, filename, stat):
        client = storage.Client(projectname)
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(filename)
        # print("{} --- {}".format(filename, blob.exists()))
        stat.append(blob.exists())
        if(not blob.exists()):
            with open('/home/sdlreco/crons/nsdl_aeps/error/missing-'+str(dates)+'.txt', 'a+') as f:
                f.write(filename)
                f.write('\n')
    bucket_name = 'sm-prod-rpa'
    stat = []
    for path in file_path:
        status(project_id,  bucket_name, path, stat)
    if False in stat:
        print('Files missing : Logged at -- /home/sdlreco/crons/nsdl_aeps/error/missing-'+str(dates)+'.txt')
    else:
        try: #Try to do reconciliation
            print('Reconciliation for: ', str(dates))
            print('All files found, Processing ...')
            # bank statement
            #log file 1
            # credentials = service_account.Credentials.from_service_account_file(key_path)
            project_id = 'spicemoney-dwh'

            client = bigquery.Client( project=project_id, location='asia-south1')

            
            #log file 1


            schema = [{'name':'bc_id','type':'STRING'},
                    {'name':'bc_name','type':'STRING'},
                    {'name':'username','type':'STRING'},
                    {'name':'terminal_id','type':'STRING'},
                    {'name':'card_no','type':'STRING'},
                    {'name':'uid_auth_code','type':'STRING'},
                    {'name':'itc','type':'STRING'},
                    {'name':'transaction_type','type':'STRING'},
                    {'name':'transaction_details','type':'STRING'},
                    {'name':'RRN','type':'STRING'},
                    {'name':'dest_stan','type':'STRING'},
                    {'name':'source_stan','type':'STRING'},
                    {'name':'transaction_amount','type':'float'},
                    {'name':'transaction_date_time','type':'TIMESTAMP'},
                    {'name':'transaction_status','type':'STRING'},
                    {'name':'host_response_code','type':'STRING'},
                    {'name':'institutionid','type':'STRING'},
                    {'name':'acquirer','type':'STRING'},
                    {'name':'bc_ref_id','type':'STRING'}]

            header_list = ['bc_id','bc_name','username','terminal_id','card_no','uid_auth_code','itc','transaction_type','transaction_details','RRN','dest_stan','source_stan','transaction_amount','transaction_date_time','transaction_status','host_response_code','institutionid','acquirer','bc_ref_id']          
            list1=['bc_id','bc_name','username','terminal_id','card_no','uid_auth_code','itc','transaction_type','transaction_details','RRN','dest_stan','source_stan','transaction_status','host_response_code','institutionid','acquirer','bc_ref_id']          
            
            df = pd.read_csv('gs://sm-prod-rpa/'+str(current_year)+'/'+str(current_month)+'/'+str(current_day)+'/NSDLAEPSTransaction Report/Daily_AEPS_Transaction_'+str(current_day9)+'-'+str(current_month_name)+'-'+str(current_year2)+'-SPICE_MONEY/Daily_AEPS_Transaction-'+str(current_day9)+'-'+str(current_month_name)+'-'+str(current_year2)+'-SPICE_MONEY.txt' ,delimiter = ",",names=header_list, dayfirst= True,index_col=False, skiprows=1 ,parse_dates = (['transaction_date_time']))
            

            df[list1]=df[list1].astype(str)
            df=df.loc[~df['transaction_amount'].isin(['Transaction Amount']) ]
            df['transaction_amount']=df['transaction_amount'].astype(float)
            df['transaction_date_time'] =  pd.to_datetime(df['transaction_date_time'], format='%d-%m-%Y %H:%M')
            #format='%d-%m-%Y %H:%M' 26-11-2022 45:35    format='%d-%m-%y %H:%M' 25-11-22 5:34
            
            pp = 'gs://sm-prod-rpa/'+str(current_year)+'/'+str(current_month)+'/'+str(current_day)+'/NSDLAEPSTransaction Report/Daily_AEPS_Transaction_'+str(current_day9)+'-'+str(current_month_name)+'-'+str(current_year2)+'-SPICE_MONEY/Daily_AEPS_Transaction_'+str(current_day9)+'-'+str(current_month_name)+'-'+str(current_year2)+'-SPICE_MONEY.txt'
            print(pp)

            df.to_gbq(destination_table='sm_recon.ts_aeps_nsdl_logs', project_id='spicemoney-dwh', if_exists='replace' , table_schema = schema)
            df.to_gbq(destination_table='prod_sm_recon.prod_aeps_nsdl_logs', project_id='spicemoney-dwh', if_exists='append' , table_schema = schema)
            
            # bank statement
            
            
            #Bank Statement
            
            schema = [{'name':'REF_TXN_NO','type':'STRING'},
                    {'name':'USRREFNO','type':'STRING'},
                    {'name':'CHANTXNREFNO','type':'STRING'},
                    {'name':'TXNDATE','type':'TIMESTAMP'},
                    {'name':'VALUEDATE','type':'DATE'},
                    {'name':'DESCRIPION','type':'STRING'},
                    {'name':'TXN_LITERAL','type':'STRING'},
                    {'name':'CHEQUE_NO','type':'STRING'},
                    {'name':'DRCR','type':'STRING'},
                    {'name':'TXNBRANCH','type':'STRING'},
                    {'name':'AMOUNT','type':'FLOAT'},
                    {'name':'OTHER_ACCOUNT','type':'STRING'},
                    {'name':'IFSC_CODE','type':'STRING'},
                    {'name':'Running_Total','type':'STRING'},
                    {'name':'NEW_CHEQUE_NO','type':'STRING'},
                    {'name':'tagging','type':'STRING'}
                      
                    ]
            header_list=['REF_TXN_NO','USRREFNO','CHANTXNREFNO','TXNDATE','VALUEDATE','DESCRIPION','TXN_LITERAL','CHEQUE_NO','DRCR','TXNBRANCH','AMOUNT','OTHER_ACCOUNT','IFSC_CODE','Running_Total','NEW_CHEQUE_NO','tagging']    
            df=pd.read_excel('gs://sm-prod-rpa/'+str(current_year)+'/'+str(current_month)+'/'+str(current_day)+'/NSDLM2B_AEPSStatement/Account_Statement_'+str(current_day9)+str(current_month_name2)+'_502000053575.xlsx',header=None,index_col=False,names=header_list,skiprows=1,sheet_name='Export Worksheet',engine="openpyxl")
            print(df.head())
            print(df.info())
            list1=['REF_TXN_NO','USRREFNO','CHANTXNREFNO','DESCRIPION','TXN_LITERAL','CHEQUE_NO','DRCR','TXNBRANCH','AMOUNT','OTHER_ACCOUNT','IFSC_CODE','Running_Total','NEW_CHEQUE_NO','tagging']
            df[list1]=df[list1].astype(str)
            df['AMOUNT']=df['AMOUNT'].astype(float)
            df['TXNDATE'] =  pd.to_datetime(df['TXNDATE'],format='%Y-%m-%d %H:%M')
            df['VALUEDATE'] =  pd.to_datetime(df['VALUEDATE'],format='%Y-%m-%d %H:%M:%S.%f').dt.date

            '''
            print(df.info())
            s1= df['DESCRIPION'].str.split("_").str[1]
            print(s1)
            conditions = [(df['DESCRIPION'].str.contains("AEPS_", na=False)) & (df['CHEQUE_NO'].str.contains("0.0",na=False))]
            values = [s1]
            df['NEW_CHEQUE_NO'] = np.select(conditions,values)
            df['NEW_CHEQUE_NO']=df['NEW_CHEQUE_NO'].astype(str)
            #cond=df['CHEQUE_NO'].str.contains("0.0",na=False)
            #df['CHEQUE_NO'] = np.select(cond,df['NEW_CHEQUE_NO'])
            df['CHEQUE_NO'] = df.apply(lambda x: x['NEW_CHEQUE_NO'] if x['CHEQUE_NO'].str.contains("0.0",na=False) else x['CHEQUE_NO'], axis=1)
            '''
			
            #CR 17th Of Jan
            #CR 9th APR 2024
            #CR 13 june 2024
            #CR 09 Oct 2024
            s2= df['DESCRIPION'].str.split("_").str[1]
            print(s2)
            conditions2 = [(df['DESCRIPION'].str.contains("AEPS_", na=False) )  & (df['CHEQUE_NO'].str.contains("0.0",na=False)) & (~df['DESCRIPION'].str.contains("AEPS_CW", na=False)) ]
            values2 = [s2]
            df['NEW_CHEQUE_NO'] = np.select(conditions2,values2)
            print(df['NEW_CHEQUE_NO'])
            df['NEW_CHEQUE_NO']=df['NEW_CHEQUE_NO'].astype(str)
            #cond=df['CHEQUE_NO'].str.contains("0.0",na=False)
            #df['CHEQUE_NO'] = np.select(cond,df['NEW_CHEQUE_NO'])
            df['CHEQUE_NO'] = df.apply(lambda x: x['NEW_CHEQUE_NO'] if x['CHEQUE_NO']==("0.0") else x['CHEQUE_NO'], axis=1)
            
            s3= df['DESCRIPION'].str.split("-").str[1]
            print(s3)
            conditions3 = [(df['DESCRIPION'].str.contains("AEPS-", na=False) | df['DESCRIPION'].str.contains("AEPS ONUS CW-", na=False) | df['DESCRIPION'].str.contains("AEPS ONUS CW -", na=False))  & (df['CHEQUE_NO'].str.contains("0",na=False)) ]
            values3 = [s3]
            df['NEW_CHEQUE_NO'] = np.select(conditions3,values3)
            print(df['NEW_CHEQUE_NO'])
            df['NEW_CHEQUE_NO']=df['NEW_CHEQUE_NO'].astype(str)
            #cond=df['CHEQUE_NO'].str.contains("0.0",na=False)
            #df['CHEQUE_NO'] = np.select(cond,df['NEW_CHEQUE_NO'])
            df['CHEQUE_NO'] = df.apply(lambda x: x['NEW_CHEQUE_NO'] if x['CHEQUE_NO']==("0") else x['CHEQUE_NO'], axis=1)
			
			#CR 18th of july 2025
            s4= df['DESCRIPION'].str.split("_").str[2]
            print(s4)
            conditions4 = [(df['DESCRIPION'].str.contains("AEPS_CW", na=False))  & (df['CHEQUE_NO'].str.contains("0",na=False)) ]
            values4 = [s4]
            df['NEW_CHEQUE_NO'] = np.select(conditions4,values4)
            print(df['NEW_CHEQUE_NO'])
            df['NEW_CHEQUE_NO']=df['NEW_CHEQUE_NO'].astype(str)
            #cond=df['CHEQUE_NO'].str.contains("0.0",na=False)
            #df['CHEQUE_NO'] = np.select(cond,df['NEW_CHEQUE_NO'])
            df['CHEQUE_NO'] = df.apply(lambda x: x['NEW_CHEQUE_NO'] if x['CHEQUE_NO']==("0") else x['CHEQUE_NO'], axis=1)
			
            conditions = [(df['DESCRIPION'].str.startswith('5020000468')) & (df['DRCR'].str.contains(pat='D')) ,
                     
                        (df['DESCRIPION'].str.startswith('AEPS Chb A')) & (df['DRCR'].str.contains(pat='D')) ,
                        (df['DESCRIPION'].str.startswith('AEPS Cred')) & (df['DRCR'].str.contains(pat='D')),
                        (df['DESCRIPION'].str.startswith('AEPS Frd C')) & (df['DRCR'].str.contains(pat='D')),
                        (df['DESCRIPION'].str.startswith('AEPS ONUS')) & (df['DRCR'].str.contains(pat='C')),
                        
                        (df['DESCRIPION'].str.startswith(pat='AEPS PENDI'))  & (df['DRCR'].str.contains(pat='C')) ,
                        (df['DESCRIPION'].str.startswith(pat='AEPS REAL'))  & (df['DRCR'].str.contains(pat='C')),
                        (df['DESCRIPION'].str.startswith(pat='AEPS TXN'))  & (df['DRCR'].str.contains(pat='C')),
                        (df['DESCRIPION'].str.startswith(pat='FT_CR'))  & (df['DRCR'].str.contains(pat='C')),
                        (df['DESCRIPION'].str.startswith(pat='FT_DR'))  & (df['DRCR'].str.contains(pat='D')),
                        (df['DESCRIPION'].str.startswith(pat='RTGS'))  & (df['DRCR'].str.contains(pat='D')),
                        (df['DESCRIPION'].str.contains(pat='Comm')) & (df['DRCR'].str.contains(pat='C')) & (~df['DESCRIPION'].str.contains('CD', na=False)),
                        (df['DESCRIPION'].str.contains('AEPS_', na=False)) & (~df['DESCRIPION'].str.contains('CD', na=False)),
                        (df['DESCRIPION'].str.contains('AEPS FRAUD', na=False)) & (df['DRCR'].str.contains(pat='D')),
						(df['DESCRIPION'].str.contains('ATM FUNDS TRANSFER using', na=False)) & (df['DRCR'].str.contains(pat='D'))
                        ]
            values = ['cash_deposit','charge back','Credit Adjustment','Debit against fraud CB','Cash Withdrawal','Cash Withdrawal',
            'Cash Withdrawal','Cash Withdrawal','funding','funding','funding','commission','Cash Withdrawal','Debit against fraud CB','cash_deposit'
                    ] 
            df['tagging'] = np.select(conditions,values)
            df=df.fillna(0.0)
            df.to_gbq(destination_table='sm_recon.ts_aeps_nsdl_bank_statement', project_id='spicemoney-dwh', if_exists='replace' , table_schema = schema)
            df.to_gbq(destination_table='prod_sm_recon.prod_aeps_nsdl_bank_statement', project_id='spicemoney-dwh', if_exists='append' , table_schema = schema)




            
            # new log table Creation
            #ts_aeps_nsdl_logs_transform
            
            sql_code1="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as(
    select date(a.transaction_date_time) as trans_date,a.bc_id,a.bc_name,
    a.username,a.bc_ref_id as bc_transaction_id ,a.transaction_type,a.RRN,a.transaction_amount,
    a.host_response_code as npciresponsecode,b.transaction_type as reversal_transaction_type,
    b.host_response_code as reversal_host_response_code, 
    from spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs a  left join spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs b
    on a.bc_ref_id=b.bc_ref_id
    where (a.transaction_type like '%Withdrawal%' and a.transaction_type not like '%reversal%'
    and b.transaction_type like '%reversal%') and date(a.transaction_date_time)= date_trunc(date_sub(@date , interval 0 day), day) and date(b.transaction_date_time)= date_trunc(date_sub(@date , interval 0 day), day) 
    ),
    cte2 as(
    select date(transaction_date_time) as trans_date,bc_id,bc_name,
    username,bc_ref_id as bc_transaction_id ,transaction_type,RRN,transaction_amount,
    host_response_code as npciresponsecode,'null' as reversal_transaction_type,
    'null' as reversal_host_response_code, 
    from spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs b 
    where transaction_type like '%Withdrawal%' and transaction_type not like '%reversal%' and 
    not exists(select a.RRN from cte1 a where b.RRN=a.RRN ) and date(b.transaction_date_time)= date_trunc(date_sub(@date , interval 0 day), day) 

    ),
    cte3 as (
    select * from cte1 union all
    select * from cte2
    ),
    cte4 as(
    select *,
    case 
       when (npciresponsecode like '0' or npciresponsecode like '00')
       and reversal_host_response_code  like 'null' then 'Success'

        when (npciresponsecode like '0' or npciresponsecode like '00') 
        and (reversal_host_response_code  like '0' or reversal_host_response_code  like '00') then 'Fail'

       when (npciresponsecode like '0' or npciresponsecode like '00') 
       and (reversal_host_response_code not like '0' or reversal_host_response_code not like '00') then 'Success' 


       when (npciresponsecode not like '0' or npciresponsecode not like '00')  then 'Fail'

    end as status from cte3
    )
    select * from cte4 
            
            
            
            """
            
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code1, job_config=job_config)
            results = query_job.result()

            #Success in Detail spice logs not credit in FtrRevoke
            #ts_aeps_nsdl_spice_detail_vs_cme_wallet
            sql_code2="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as(
            select 
                  date(a.log_date_time) as LOG_DATE_TIME,CLIENT_ID,
                  SPICE_TID,sum(trans_amt) as SUM_OF_TRANS_AMOUNT,
                  jdt_stan as JDT_STAN,response_code as RC,
                  response_message as MESSAGE,a.aggregator 
            from `spicemoney-dwh.prod_dwh.aeps_trans_req` a  
            join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b 
            on a.request_id=b.request_id 
            where date(a.log_date_time)= date_trunc(date_sub(@date , interval 0 day), day)   
            and b.rc='00'  and date(b.log_date_time)= date_trunc(date_sub(@date , interval 0 day), day)  
            and a.aggregator='NSDL' and master_trans_type='CW' 
            group by LOG_DATE_TIME,CLIENT_ID,SPICE_TID,JDT_STAN,RC,MESSAGE,aggregator
    ),

    cte2 as(
             select *
             from `spicemoney-dwh.prod_dwh.cme_wallet` 
             where date(transfer_date)= date_trunc(date_sub(@date , interval 0 day), day) 
             and (comments like 'AEPS RBL- Cash Withdrawal' or comments like ' AEPS-CASH WITHDRAWAL-MANUAL-CREDIT') 

    ),
    cte3 as (
            select 
               a.LOG_DATE_TIME,a.CLIENT_ID,a.SPICE_TID,a.SUM_OF_TRANS_AMOUNT,a.JDT_STAN,
               a.RC,a.MESSAGE ,b.unique_identification_no as FTR_ID,a.aggregator ,amount_transferred
            from cte1 a 
            left join cte2 b 
            on a.spice_tid=b.unique_identification_no

    )
    select * from cte3 where   FTR_ID is null
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_spice_detail_vs_cme_wallet', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code2, job_config=job_config)
            results = query_job.result()

            #Credit in FtrRevoke failed/Not in Spice detail logs
            #ts_aeps_nsdl_cme_wallet_vs_spice_detail
            
            sql_code3="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as(
     select unique_identification_no as Unique_Identification_No,amount_transferred as Amount_Transferred ,date(transfer_date) as
     Transfer_date,distributor_retailer_trans_id,transfer_mode,trans_type,comments,ip_address,distr_wallet_id
       from `spicemoney-dwh.prod_dwh.cme_wallet` 
       where date(transfer_date)=date_trunc(date_sub(@date , interval 0 day), day)  and (comments like 'AEPS RBL- Cash Withdrawal' or comments like ' AEPS-CASH WITHDRAWAL-MANUAL-CREDIT'
       )
    ),
    cte2 as(

    select date(a.log_date_time) as LOG_DATE_TIME,CLIENT_ID,SPICE_TID,sum(trans_amt) as SUM_OF_TRANS_AMOUNT,jdt_stan as JDT_STAN,
     response_code as RC,
    response_message as MESSAGE,a.aggregator 
    from `spicemoney-dwh.prod_dwh.aeps_trans_req` a join
    `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b on a.request_id=b.request_id 
    where date(a.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day) and date(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)  and rc!='00'  and
    a.aggregator='NSDL' and master_trans_type='CW' 
    group by LOG_DATE_TIME,CLIENT_ID,SPICE_TID,JDT_STAN,RC,MESSAGE,aggregator

    ),
    cte3 as(
      select a.Unique_Identification_No,a.Amount_Transferred,a.Transfer_date,a.distributor_retailer_trans_id,b.aggregator,
      a.transfer_mode,a.comments,a.ip_address,a.distr_wallet_id,b.SPICE_TID as SPICE_DETAIL_LOGS_TID,b.RC as SPICE_DETAIL_LOGS_RESPONSE
      from cte1 a left join cte2 b on a.Unique_Identification_No=b.SPICE_TID 
      where (a.comments like 'AEPS RBL- Cash Withdrawal' or a.comments like ' AEPS-CASH WITHDRAWAL-MANUAL-CREDIT'
       ) and b.aggregator='NSDL'
    )
    select * from cte3
            
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_cme_wallet_vs_spice_detail', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code3, job_config=job_config)
            results = query_job.result()
            
            
            #Success in NSDL Txn Logs not/Fail in Spice detail logs
            #ts_aeps_nsdl_logs_vs_spice_detail
            
            sql_code4="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as(
    select * from (
                 select 
                      RRN as BankadjRef,trans_date as Date , transaction_amount as Adjamt, 
                      replace(bc_transaction_id,"'",'') as BC_Txn_ID,npciresponsecode as NSDL_Response,
                      bc_name as Filename, 
                  from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
                  where date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day) and status ='Success'
                  )  
    ),
    cte2 as(
     
     select * from (
                  select 
                                            a.*,b.*
                                       
                  from `spicemoney-dwh.prod_dwh.aeps_trans_req` a 
                  join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b 
                  on a.request_id=b.request_id 
                  where date(a.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
                  and 
                  date(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
                   and b.rc='00' and
                  a.aggregator='NSDL' and master_trans_type='CW'  
                  ) where rc!='00'
    ),
    cte3 as(
      select rc as Spice_Detail_Logs_Response ,kotak_rrn as Spice_RRN , trans_amt,rc from cte2
    ),
    cte4 as(
      select a.* ,b.* from cte1 a left join cte3 b on a.BankadjRef=b.Spice_RRN
    )
    select * from cte4  where (Spice_Detail_Logs_Response!='00'  or Spice_Detail_Logs_Response is not null)
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs_vs_spice_detail', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code4, job_config=job_config)
            results = query_job.result()
            
            #Success Txns in  NSDL Txn logs Failed/Not Present in spice detail logs
            #ts_aeps_nsdl_logs_vs_spice_detail_not_present
            
            sql_code5="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as
    (select * from (             select                 
     RRN as BankadjRef,trans_date as Date , 
    transaction_amount as Adjamt,                  
    replace(bc_transaction_id,"'",'') as BC_Txn_ID,npciresponsecode as 
    NSDL_Response,                  bc_name as Filename,              
    from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform`       
           where date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day)              
     and status ='Success'               )),cte2 as(  select * from (    
              select                                       
      a.*,b.*,b.request_id as rqid                           
            from `spicemoney-dwh.prod_dwh.aeps_trans_req` a           
       join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b          
        on a.request_id=b.request_id            
      where date(a.log_date_time)=
    date_trunc(date_sub(@date , interval 0 day), day)
     and date(b.log_date_time)=
    date_trunc(date_sub(@date , interval 0 day), day)    
       and a.aggregator='NSDL' and master_trans_type='CW'    
                            )),cte3 as(  
    select rc as Spice_Detail_Logs_Response ,kotak_rrn as Spice_RRN 
    ,rqid, trans_amt,rc,cte2.spice_tid,cte2.response_code     from cte2),
    cte4 as(  select a.* ,b.* from cte1 a left join cte3 b 
    on a.BC_Txn_ID=b.rqid)select * from cte4  where   
    (rqid is not null and Spice_Detail_Logs_Response!='00') or
     rqid  is  null
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs_vs_spice_detail_not_present', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code5, job_config=job_config)
            results = query_job.result()
            
            sql_code5_1="""
            -- AEPS NSDL RECO QUERY
           
            with cte1 as(
      select * from `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs` where date(transaction_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
    ),
    cte2 as(
      select * from spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs_vs_spice_detail_not_present where Date=date_trunc(date_sub(@date , interval 0 day), day)
    ),
    cte3 as(
      select a.* from cte1 a  join cte2 b on a.RRN=substring(BankadjRef, 1,12)
    )
    select @date as reco_date ,* from cte3
            """

            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_credit_adjustment', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            query_job = client.query(sql_code5_1, job_config=job_config)
            results = query_job.result()

            
            #Success in NSDL Txn logs not Credit in Bank
            #ts_aeps_nsdl_logs_vs_bank_statement_not_ctedit
            
            sql_code6="""
            -- AEPS NSDL RECO QUERY
            
            
            with cte1 as(
                 select 
                      RRN ,trans_date as Date , transaction_amount as Adjamt, replace(bc_transaction_id,"'",'') as BC_Txn_ID,
                      npciresponsecode as NSDL_Response 
                   from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
                   where date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day)
                   and status='Success' 
    ),
    cte2 as(
                SELECT 
                      AMOUNT as Bank_Credit_Amt ,substring(CHEQUE_NO,1,12) as Bank_RRN  
                      FROM `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement` 
                where  tagging ='Cash Withdrawal'
                and   date(TXNDATE) =date_trunc(date_sub(@date , interval 0 day), day)
                order by Bank_RRN 

    ),

    cte3 as(
      select a.* ,b.Bank_Credit_Amt,b.Bank_RRN as Bank_RRN from cte1 a left join cte2 b on a.RRN=b.Bank_RRN
    )
    select 
    *
    --sum(Adjamt) 
    from cte3 
    where Bank_RRN is null  
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs_vs_bank_statement_not_ctedit', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code6, job_config=job_config)
            results = query_job.result()
            
            #Not present in NSDL Txn logs But Credit in Bank
            #ts_aeps_nsdl_logs_vs_bank_statement_credit
            sql_code7="""
            -- AEPS NSDL RECO QUERY
            
            
            with cte1 as(
     
      SELECT date(TXNDATE) as Date,sum(AMOUNT) as Bank_Credit_Amt ,substring(CHEQUE_NO,1,12) as Bank_RRN  FROM `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement` 
     where  tagging in ('Cash Withdrawal')
     and   date(TXNDATE) =date_trunc(date_sub(@date , interval 0 day), day) 
     group by Date,Bank_RRN
     
    ),
    cte2 as(
      
     select RRN as NSDL_Logs_RRN ,trans_date as Date , transaction_amount as Adjamt, bc_transaction_id as BC_Txn_ID,
     npciresponsecode as NSDL_Response ,status
       from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
       where date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day)   
      
       
    ),
    cte3 as(
      select a.Bank_RRN,a.Date,b.Adjamt,b.NSDL_Logs_RRN,b.NSDL_Response,a.Bank_Credit_Amt,b.status from cte1 a left join
      cte2 b on a.Bank_RRN=b.NSDL_Logs_RRN where b.NSDL_Logs_RRN is null 
    )
    select 
    *
    --sum(Bank_Credit_Amt) 
    from cte3 

            
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs_vs_bank_statement_credit', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code7, job_config=job_config)
            results = query_job.result()
            
            #Fail in NSDL Txn logs But Credit in Bank
            #ts_aeps_nsdl_logs_vs_bank_statement_nsdl_fail
            
            sql_code8="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as(
     
      SELECT date(TXNDATE) as Date,sum(AMOUNT) as Bank_Credit_Amt ,substring(CHEQUE_NO,1,12) as Bank_RRN  FROM `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement` 
     where  tagging in ('Cash Withdrawal')
     and   date(TXNDATE) =date_trunc(date_sub(@date , interval 0 day), day)
     group by Date,Bank_RRN
     
    ),
    cte2 as(
     select RRN as NSDL_Logs_RRN ,trans_date as Date , transaction_amount as Adjamt, bc_transaction_id as BC_Txn_ID,
     npciresponsecode as NSDL_Response ,
     status
       from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
       where date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day)  and status ='Fail'
        
       
    ),
    cte3 as(
      select a.Bank_RRN,a.Date,b.Adjamt,b.NSDL_Logs_RRN,b.NSDL_Response,a.Bank_Credit_Amt,b.status from cte1 a  join
      cte2 b on a.Bank_RRN=b.NSDL_Logs_RRN --where b.NSDL_Logs_RRN is null 
    )
    select 
    *
    from cte3 
            
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs_vs_bank_statement_nsdl_fail', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code8, job_config=job_config)
            results = query_job.result()
            
            #NSDL Report and Spice report gap
            #ts_aeps_nsdl_report_vs_spice_report_gap
            
            sql_code9="""
            -- AEPS NSDL RECO QUERY
            
            with cte1 as(

                      select 
                          date(log_date_time) as Date,
                          RRN as NSDL_RRN,sum(transaction_amount) as NSDL_Amt,b.kotak_rrn as Spice_RRN ,
                          sum(amount) as Spice_Amt,(sum(transaction_amount)-sum(amount)) as Diff
                      from (
                              select date(trans_date) as trans_date,status,RRN,
                                     sum(transaction_amount) as transaction_amount 
                              from  `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
                                group by trans_date,RRN,status) as a
                      full outer join  (
                                        select kotak_rrn,sum(amount) as amount,
                                         date(log_date_time) as log_date_time,
                                        from  `spicemoney-dwh.prod_dwh.aeps_trans_res_v2`
                                        where rc='00'
                                        group by kotak_rrn,log_date_time
                                        
                                        ) b
                      on a.RRN = b.kotak_rrn  
                      where date(trans_date) = date_trunc(date_sub(@date , interval 0 day), day) and 
                      date(log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)
                      and status='Success'  
                      group by Date,RRN,b.kotak_rrn
    )
    select  * from cte1
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_report_vs_spice_report_gap', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code9, job_config=job_config)
            results = query_job.result()
            
            
            #Bank Summary
            #ts_aeps_nsdl_bank_summary
            
            sql_code10="""
            -- AEPS NSDL RECO QUERY
            
            
            select date(TXNDATE) as Date_,tagging ,DRCR ,sum(AMOUNT) as Amount FROM `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement`
    where date(TXNDATE)=date_trunc(date_sub(@date , interval 0 day), day)
    group by tagging ,DRCR,Date_
    order by Date_
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_summary', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code10, job_config=job_config)
            results = query_job.result()
            
            #NSDL Report and Bank statement gap and Bank statement and NSDL report Gap
            #ts_aeps_nsdl_report_vs_bank_bank_report_gap_vice_versa
            sql_code11="""
            -- AEPS NSDL RECO QUERY
            
            select * from (
    select
    Date,BankadjRef,nsdlAdjamt,Bank_RRN,Bank_Credit_Amt,(Bank_Credit_Amt-nsdlAdjamt) as Diff
    from (
    select 
    case 
       when Date is null then TXNDATE
       when TXNDATE is null then Date
       else Date
    end as Date,   
    BankadjRef,	coalesce(sum(Adjamt),0) as nsdlAdjamt, 	Bank_RRN,coalesce(sum(Bank_Credit_Amt),0) as Bank_Credit_Amt
    from (


                  select 
                      RRN as BankadjRef,trans_date as Date , transaction_amount as Adjamt, 
                      replace(bc_transaction_id,"'",'') as BC_Txn_ID,npciresponsecode as NSDL_Response,
                      bc_name as Filename, 
                  from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
                  where  date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day) and status ='Success'
                  --and RRN='220207462089'
                  
                  
                  ) as  a
                  full outer join 
                  (
                SELECT 
                      sum(AMOUNT) as Bank_Credit_Amt ,substring(CHEQUE_NO,1,12) as Bank_RRN ,date(TXNDATE) as TXNDATE 
                      FROM `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement` 
                where  tagging ='Cash Withdrawal' 
                --and            substring(CHEQUE_NO,1,12)='220207462089'
                and   date(TXNDATE) =date_trunc(date_sub(@date , interval 0 day), day)
                group by Bank_RRN ,TXNDATE
                order by Bank_RRN 
    ) as b 
    on substring(a.BankadjRef,1,12) = b.Bank_RRN

    group by Date,BankadjRef,Bank_RRN
    ))
    where (BankadjRef is null or Bank_RRN is null  or (Diff>0 or diff<0))

            
            
            """
            
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_report_vs_bank_bank_report_gap_vice_versa', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code11, job_config=job_config)
            results = query_job.result()
            
            #NSDL Raw Logs Figures
            #ts_aeps_nsdl_raw_logs_figures
            
            sql_code12="""
            -- AEPS NSDL RECO QUERY
            
            select date(transaction_date_time) as Date_,sum(transaction_amount ) as Amount,host_response_code 
    from `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs`
    where transaction_type  like '%Withdrawal%' and  date(transaction_date_time) =date_trunc(date_sub(@date , interval 0 day), day)
    group by Date_,host_response_code
    order by Date_
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_raw_logs_figures', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code12, job_config=job_config)
            results = query_job.result()
            
            
            #Spice Vs Nsdl Mini Statement Exceptions
            
            #ts_aeps_nsdl_spice_vs_nsdl_ministatement_exception
            
            sql_code13="""
            -- AEPS NSDL RECO QUERY
            
            
            select 
      case when Date_ is null then LOG_DATE_TIME
           when LOG_DATE_TIME is null then Date_
           else Date_
      end as Date_     ,RRN,bc_ref_id,JDT_STAN,SPICE_TID,client_id 
    from (

    select  date(transaction_date_time) as Date_,RRN  ,replace(bc_ref_id,"'",'') as bc_ref_id 
    from `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs`
    where transaction_type  like '%Mini%' and (host_response_code ='0' or host_response_code ='00') 
    and date(transaction_date_time)=date_trunc(date_sub(@date , interval 0 day), day) 
    group by Date_,RRN,bc_ref_id 
    order by Date_

    ) as a 
    full outer join (

     select 
                  date(a.log_date_time) as LOG_DATE_TIME,CLIENT_ID,
                  SPICE_TID,sum(trans_amt) as SUM_OF_TRANS_AMOUNT,
                  jdt_stan as JDT_STAN,response_code as RC,
                  response_message as MESSAGE,a.aggregator 
            from `spicemoney-dwh.prod_dwh.aeps_trans_req` a  
            join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b 
            on a.request_id=b.request_id 
            where date(a.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day) 
            and b.rc='00'  and date(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)  
            and a.aggregator='NSDL' and master_trans_type='MS' 
            group by LOG_DATE_TIME,CLIENT_ID,SPICE_TID,JDT_STAN,RC,MESSAGE,aggregator
      ) as b 
      on a.RRN = b.JDT_STAN
      where a.RRN is null or b.JDT_STAN is null
      group by Date_,RRN,bc_ref_id,JDT_STAN,SPICE_TID,client_id 
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_spice_vs_nsdl_ministatement_exception', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code13, job_config=job_config)
            results = query_job.result()
            
            
            #NSDL Report and Spice report gap and Spice Report and NSDL report Gap
            
            #ts_aeps_nsdl_report_vs_spice_report_gap_vice_versa
            print("sql_code 14 start")
            sql_code14="""
            -- AEPS NSDL RECO QUERY
            
            
            select 
    case when LOG_DATE_TIME is null then  Date
        when Date is null then LOG_DATE_TIME 
        else LOG_DATE_TIME end as Date,JDT_STAN,sum(SUM_OF_TRANS_AMOUNT) as SDL_Amount,BankadjRef,sum(Adjamt) as Adjamt 
    from (
           select 
                  date(a.log_date_time) as LOG_DATE_TIME,CLIENT_ID,
                  SPICE_TID,sum(trans_amt) as SUM_OF_TRANS_AMOUNT,
                  jdt_stan as JDT_STAN,response_code as RC,
                  response_message as MESSAGE,a.aggregator 
            from `spicemoney-dwh.prod_dwh.aeps_trans_req` a  
            join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b 
            on a.request_id=b.request_id 
            where date(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)  
            and b.rc='00'  and date(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)  
            and a.aggregator='NSDL' and master_trans_type='CW' 
            group by LOG_DATE_TIME,CLIENT_ID,SPICE_TID,JDT_STAN,RC,MESSAGE,aggregator

    ) as a 
    full outer join (
                 select 
                      RRN as BankadjRef,trans_date as Date , transaction_amount as Adjamt, 
                      replace(bc_transaction_id,"'",'') as BC_Txn_ID,npciresponsecode as NSDL_Response,
                      bc_name as Filename, 
                  from `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform` 
                  where date(trans_date)=date_trunc(date_sub(@date , interval 0 day), day) and status ='Success'
    ) as b 
    on a.SPICE_TID = b.BC_Txn_ID 
    where a.JDT_STAN is null or BankadjRef is null  
    group by Date ,JDT_STAN,BankadjRef
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_report_vs_spice_report_gap_vice_versa', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code14, job_config=job_config)
            results = query_job.result()
            
            #Min Max CW Amount
            
            #ts_aeps_nsdl_min_max_cw_amount
            print("sql_code 15 start")
            sql_code15="""
            -- AEPS NSDL RECO QUERY
            
            
            select * from (
      select @date as recon_date,spice_tid ,min(a.trans_amt ) as Amount
            from `spicemoney-dwh.prod_dwh.aeps_trans_req` a  
            join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b 
            on a.request_id=b.request_id 
            where date(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)  
            and b.rc='00'  and date(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)  
            and a.aggregator='NSDL' and master_trans_type='CW' 
            group by spice_tid
            order by Amount limit 1
     ) union all 
     (
     
       select @date as recon_date,spice_tid ,max(a.trans_amt ) as Amount
            from `spicemoney-dwh.prod_dwh.aeps_trans_req` a  
            join `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b 
            on a.request_id=b.request_id 
            where date(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day) 
            and b.rc='00'  and date(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)  
            and a.aggregator='NSDL' and master_trans_type='CW' 
            group by spice_tid
            order by Amount desc limit 1
     
     )
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_min_max_cw_amount', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code15, job_config=job_config)
            results = query_job.result()

            print("sql_code 16 start")
            # ts_aeps_nsdl_recon_tracker
            sql_code16= """
            -- AEPS NSDL RECO QUERY
            WITH
cte1a as(
SELECT
        DATE(a.log_date_time) AS Date_aa,
        COUNT(kotak_rrn) AS Txn_Count_as_per_Detailed_Logs_new
        FROM
        `spicemoney-dwh.prod_dwh.aeps_trans_req` a
      JOIN
        `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b
      ON
        a.request_id=b.request_id
      WHERE
        DATE(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)
        AND b.rc='00'
        AND DATE(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
        AND a.aggregator='NSDL'
        AND master_trans_type='CW'
		
      GROUP BY
        Date_aa 
),

      cte1 AS (
      SELECT
        DATE(a.log_date_time) AS Date,
        COUNT(kotak_rrn) AS Txn_Count_as_per_Detailed_Logs,
        CAST(SUM(CASE
              WHEN trans_amt*0.005>15  THEN 15
            ELSE
            trans_amt*0.005
          END
            ) AS int64) AS Total_amount_eligible_for_SDL_Payout,
        CAST(SUM(CASE
              WHEN trans_amt*0.005>15 THEN 15
            ELSE
            trans_amt*0.005
          END
            )*0.95 AS int64) AS SDL_Share,
        CAST(SUM(CASE
              WHEN trans_amt*0.005>15 THEN 15
            ELSE
            trans_amt*0.005
          END
            )*0.95*1.18 AS int64) AS SDL_Share_with_gst,
      FROM
        `spicemoney-dwh.prod_dwh.aeps_trans_req` a
      JOIN
        `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b
      ON
        a.request_id=b.request_id
      WHERE
        DATE(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)
        AND b.rc='00'
        AND DATE(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
        AND a.aggregator='NSDL'
        AND master_trans_type='CW'
		AND cust_bank_name not like "NSDL Payments Bank Limited "
      GROUP BY
        Date ),
      cte2 AS(
      SELECT
        DATE(transfer_date) AS cme_date,
        CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Alliance Transaction Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS aeps_alliance_commission,
        CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Transaction Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS aeps_agent_transaction_commission,
        CAST(SUM(CASE
              WHEN comments in ('AEPS RBL Distr Transaction Commission', 'AEPS-CW Dist Commission', 'AEPS-CW Partner Commission', 'Multiplier slab_AEPS_Commission', 'Multiplier slab_AEPS_Partner_Commission', 'AEPS-CW Super Partner Commission')  THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) -
            
        CAST(SUM(CASE
              WHEN comments in ('Multiplier slab_AEPS_Commission_revised', 'Multiplier slab_AEPS_Partner_Commission_revised')  THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS aeps_distr_transaction_commission,
        CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Sub Distr Transaction Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS aeps_sub_distr_transaction_commission,
        CAST(SUM(CASE
              WHEN comments = 'AEPS-CW Partner Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS AEPS_CW_Partner_Commission,
        CAST(SUM(CASE
              WHEN comments = 'AEPS-CW Super Partner Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS AEPS_CW_Super_Partner_Commission,
        CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Alliance Transaction Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64)+ CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Transaction Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64)+ CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Distr Transaction Commission' OR comments = 'AEPS-CW Dist Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64)+ CAST(SUM(CASE
              WHEN comments = 'AEPS RBL Sub Distr Transaction Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64)+ CAST(SUM(CASE
              WHEN comments = 'AEPS-CW Partner Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64)+ CAST(SUM(CASE
              WHEN comments = 'AEPS-CW Super Partner Commission' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS total_commission_credited,
        CAST(SUM(CASE
              WHEN comments = 'AEPS RBL- Cash Withdrawal' OR comments = ' AEPS-CASH WITHDRAWAL-MANUAL-CREDIT' THEN amount_transferred
            ELSE
            0
          END
            ) AS int64) AS ftr_agent_wallet_credit_amount,
      FROM
        `spicemoney-dwh.prod_dwh.cme_wallet` a
      JOIN (
        SELECT
          SPICE_TID
        FROM
          spicemoney-dwh.prod_dwh.aeps_trans_req a
        JOIN
          spicemoney-dwh.prod_dwh.aeps_trans_res_v2 b
        ON
          a.request_id=b.request_id
        WHERE
          DATE(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)
          AND b.rc='00'
          AND DATE(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
          AND a.aggregator='NSDL'
          AND master_trans_type='CW' ) AS b
      ON
        a.unique_identification_no = b.spice_tid
      WHERE
        DATE(transfer_date)=date_trunc(date_sub(@date , interval 0 day), day)
      GROUP BY
        cme_date ),
      cte3 AS(
      SELECT
        DATE(a.log_date_time) AS cte3_Date,
        SUM(trans_amt) AS Amt_as_per_Details_Logs_sdl
      FROM
        `spicemoney-dwh.prod_dwh.aeps_trans_req` a
      JOIN
        `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b
      ON
        a.request_id=b.request_id
      WHERE
        DATE(a.log_date_time) =date_trunc(date_sub(@date , interval 0 day), day)
        AND b.rc='00'
        AND DATE(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
        AND a.aggregator='NSDL'
        AND master_trans_type='CW'
      GROUP BY
        cte3_Date ),
      cte4 AS(
      SELECT
        trans_date AS cte4_Date,
        SUM(transaction_amount) AS Amt_as_per_NSDL_Recon_File,
      FROM
        `spicemoney-dwh.sm_recon.ts_aeps_nsdl_logs_transform`
      WHERE
        DATE(trans_date)=date_trunc(date_sub(@date , interval 0 day), day)
        AND status='Success'
      GROUP BY
        cte4_Date ),
      cte5 AS(
      SELECT
        DATE(TXNDATE) AS cte5_date,
        CAST(SUM(CASE
              WHEN tagging ='Cash Withdrawal' 
              --AND LENGTH(SUBSTRING(CHEQUE_NO,1,12))=12 
              AND DRCR='C' THEN AMOUNT
            ELSE
            0
          END
            ) AS int64) AS Amt_as_per_Bank_Statement_credit,
        CAST(SUM(CASE
              WHEN tagging ='Credit Adjustment' THEN AMOUNT
            ELSE
            0
          END
            ) AS int64) AS Amt_as_per_Bank_Statement_Credit_Adjustments_processed,
        CAST(SUM(CASE
              WHEN tagging ='Debit against fraud CB' THEN AMOUNT
            ELSE
            0
          END
            ) AS int64) AS Chargeback_or_Fraud_Adjustments,
        CAST(SUM(CASE
              WHEN DRCR ='C' AND tagging='commission' THEN AMOUNT
            ELSE
            0
          END
            ) AS int64) AS Amt_Credited_as_per_Bank_Statement
      FROM
        `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement`
      WHERE
        DATE(TXNDATE) =date_trunc(date_sub(@date , interval 0 day), day)
      GROUP BY
        cte5_Date ),
      cte6 AS(
      SELECT
        DATE(transaction_date_time) AS cte6_date,
        COUNT(*) AS Mini_Statement_Txn_count_as_per_NSDL
      FROM
        `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_logs`
      WHERE
        transaction_type LIKE '%Mini%'
        and transaction_type not like "Onus Mini-Statement"
        AND (host_response_code ='0'
          OR host_response_code ='00')
        AND DATE(transaction_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
      GROUP BY
        cte6_date ),
      cte7 AS(
      SELECT
        DATE(a.log_date_time) AS cte7_Date,
        COUNT(*) AS Mini_Statement_Txn_count_as_per_Spice
      FROM
        `spicemoney-dwh.prod_dwh.aeps_trans_req` a
      JOIN
        `spicemoney-dwh.prod_dwh.aeps_trans_res_v2` b
      ON
        a.request_id=b.request_id
      WHERE
        DATE(a.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
        AND
        DATE(b.log_date_time)=date_trunc(date_sub(@date , interval 0 day), day)
        AND cust_bank_name not like "NSDL Payments Bank Limited "
        AND b.rc='00'
        AND a.aggregator='NSDL'
        AND master_trans_type='MS'
      GROUP BY
        cte7_Date ),
      cte8 AS(
      SELECT
      aa.*,
        a.*,
        b.*,
        c.*,
        (b.ftr_agent_wallet_credit_amount-c.Amt_as_per_Details_Logs_sdl) AS diff_ftr_vs_sdl_log,
        d.*,
        (e.Amt_as_per_Bank_Statement_credit-d.Amt_as_per_NSDL_Recon_File) AS Diff_NSDL_Logs_vs_Amount_settled_in_Bank,
        (e.Amt_as_per_Bank_Statement_credit-c.Amt_as_per_Details_Logs_sdl) AS Excess_settled_by_NSDL_Bank_statement,
        (d.Amt_as_per_NSDL_Recon_File-c.Amt_as_per_Details_Logs_sdl) AS Excess_settled_by_NSDL_NSDL_Logs,
        0 AS Credit_in_Bank_against_CW_NSDL_On_Us_Txns,
        ((e.Amt_as_per_Bank_Statement_credit-c.Amt_as_per_Details_Logs_sdl)-(e.Amt_as_per_Bank_Statement_Credit_Adjustments_processed+e.Chargeback_or_Fraud_Adjustments)) AS Diff_SDL_vs_NSDL_After_Adjustments,
        a.Total_amount_eligible_for_SDL_Payout AS Total_amount_eligible_for_SDL_Payout_2,
        a.SDL_Share AS SDL_Share_cd_cw,
        a.SDL_Share*0.05 AS TDS_Deduction,
        a.SDL_Share_with_gst AS SDL_Share_with_gst_2,
        (a.SDL_Share-a.SDL_Share*0.05) AS Settlement_charges_to_be_Cr_by_NSDL,
         ((a.SDL_Share-a.SDL_Share*0.05)*0.1 ) AS settlement_hold_by_NSDL_10_perc,
         ((a.SDL_Share-a.SDL_Share*0.05)+((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05))) AS Net_Income_credited_as_on_date,
        (a.SDL_Share_with_gst-a.SDL_Share+(((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05))*0.18)) AS GST_on_Settlement,
        0 AS GST_Credit_in_Bank_ac,
        ( e.Amt_Credited_as_per_Bank_Statement-((a.SDL_Share-a.SDL_Share*0.05)+((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05)))) -((a.SDL_Share_with_gst-a.SDL_Share+(((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05))*0.18))) AS Diff_SDL_vs_Bank_Statement_Income_GST,
        e.*,
        f.*,
        (f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05) AS TDS_on_Income_5_perc,
        (f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95) AS Mini_Statement_Income,
        ((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05)) AS Mini_Statement_Income_excluding_tds,
        (((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05))*0.18) AS GST_on_Income,
        (((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)+(((f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95)-(f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05))*0.18))- (f.Mini_Statement_Txn_count_as_per_NSDL*3*0.95*0.05)) AS SDL_income_with_GST,
        g.Mini_Statement_Txn_count_as_per_Spice AS Mini_Statement_Txn_count_as_per_Spice,
        (f.Mini_Statement_Txn_count_as_per_NSDL-g.Mini_Statement_Txn_count_as_per_Spice) AS Diff_Spice_vs_NSDL_Count,
      FROM
      cte1a aa
      join 
        cte1 a
        on aa.Date_aa =a.Date
      JOIN
        cte2 b
      ON
        a.Date=b.cme_date
      JOIN
        cte3 c
      ON
        a.Date=c.cte3_Date
      JOIN
        cte4 d
      ON
        a.Date=d.cte4_Date
      JOIN
        cte5 e
      ON
        a.Date=e.cte5_Date
      JOIN
        cte6 f
      ON
        a.Date=f.cte6_Date
      JOIN
        cte7 g
      ON
        a.Date=g.cte7_date ),
    cte9 as(
    SELECT
      Date,
      Txn_Count_as_per_Detailed_Logs_new Txn_Count_as_per_Detailed_Logs,
      -- Txn_Count_as_per_Detailed_Logs,
      Total_amount_eligible_for_SDL_Payout,
      SDL_Share,
      SDL_Share_with_gst,
      aeps_alliance_commission,
      aeps_agent_transaction_commission,
      aeps_distr_transaction_commission,
      aeps_sub_distr_transaction_commission,
      AEPS_CW_Partner_Commission,
      AEPS_CW_Super_Partner_Commission,
      total_commission_credited,
      ftr_agent_wallet_credit_amount,
      Amt_as_per_Details_Logs_sdl,
      diff_ftr_vs_sdl_log,
      Amt_as_per_NSDL_Recon_File,
      Amt_as_per_Bank_Statement_credit,
      Diff_NSDL_Logs_vs_Amount_settled_in_Bank,
      Excess_settled_by_NSDL_Bank_statement,
      Excess_settled_by_NSDL_NSDL_Logs,
      Amt_as_per_Bank_Statement_Credit_Adjustments_processed,
      Chargeback_or_Fraud_Adjustments,
      Credit_in_Bank_against_CW_NSDL_On_Us_Txns,
      Diff_SDL_vs_NSDL_After_Adjustments,
      Total_amount_eligible_for_SDL_Payout_2,
      SDL_Share_cd_cw,
      TDS_Deduction,
      SDL_Share_with_gst_2,
      Settlement_charges_to_be_Cr_by_NSDL,
      Net_Income_credited_as_on_date,
      Amt_Credited_as_per_Bank_Statement,
      GST_on_Settlement,
      GST_Credit_in_Bank_ac,
      Diff_SDL_vs_Bank_Statement_Income_GST,
      Mini_Statement_Txn_count_as_per_NSDL,
      TDS_on_Income_5_perc,
      Mini_Statement_Income,
      Mini_Statement_Income_excluding_tds,
      GST_on_Income,
      SDL_income_with_GST,
      Mini_Statement_Txn_count_as_per_Spice,
      Diff_Spice_vs_NSDL_Count,
    FROM
      cte8)
    select * from cte9         
            """
            
            
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_recon_tracker', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code16, job_config=job_config)
            results = query_job.result()
            print("sql_code 16 end")
            
            sql_code17="""
            -- AEPS NSDL RECO QUERY
            
            select * FROM `spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_statement` 
            where date(TXNDATE)=date_trunc(date_sub(@date , interval 0 day), day)and tagging="0"
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_bank_satement_tagging_zero', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code17, job_config=job_config)
            results = query_job.result()
            
            
            sql_code18="""
            -- AEPS NSDL RECO QUERY
            
            SELECT * FROM `spicemoney-dwh.sm_recon.ts_aeps_nsdl_bank_statement` 
            where date(TXNDATE) != date(VALUEDATE) 
            
            """
            job_config = bigquery.QueryJobConfig(destination='spicemoney-dwh.prod_sm_recon.prod_aeps_nsdl_non_recon_date_credit_debit_in_bank', write_disposition='WRITE_APPEND' ,  query_parameters=[
            bigquery.ScalarQueryParameter("date", "DATE" , current_date)])
            
            query_job = client.query(sql_code18, job_config=job_config)
            results = query_job.result()
            

            print('Recon Success for {} at {}'.format(dates, times))
            with open('/home/sdlreco/crons/nsdl_aeps/stat/stat-'+str(dates)+'.txt', 'w') as f:
                f.write('1')
                f.close()
            for ids in nsdl_aeps:

                smarten.payload(ids)
            print('Refreshed : nsdl_aeps')
            
        except Exception as e: #shows the error
            with open('/home/sdlreco/crons/nsdl_aeps/stat/error/stat-'+str(dates)+'.txt', 'w') as f:
              f.write('1')
              f.close()
            print('Error in reconciliation process!', '\nerror:', e)

#main()
#driver

import sys
sys.path.insert(0, '/home/sdlreco/crons/smarten/')
import payload as smarten


nsdl_aeps = ['1814cf328d2','1814d000592','1814d2861f3','1814d302fd6','181a5218e3d','181588f50c7','1815897ab4c','18158a43c1a','181d79e0c4e','18158afa8a8','18158b46acf','1815b1de1f2','1815b292325','1815b33b117','1815b3851ac','1815b41c8c1','1821b51f891','1907c1471e4']

for i in range(5,-1,-1):
    dates = d.today()-timedelta(i) 
    times = datetime.now()-timedelta(i)
    
    f = open('/home/sdlreco/crons/nsdl_aeps/stat/stat-'+str(dates)+'.txt', 'a+')
    f.close()
    f = open('/home/sdlreco/crons/nsdl_aeps/stat/error/stat-'+str(dates)+'.txt', 'a+')
    f.close()
    with open('/home/sdlreco/crons/nsdl_aeps/stat/stat-'+str(dates)+'.txt', 'r') as f:
        lines = f.read().splitlines()
        f.close()
        
    with open('/home/sdlreco/crons/nsdl_aeps/stat/error/stat-'+str(dates)+'.txt', 'r') as f:
        error_lines = f.read().splitlines()
        f.close()
        
        print('\n\n*******************\nReconciliation for: ', str(dates))
        if('1' in lines):
            print('Tried at {}, but reco already done !!'.format(times))
        elif('1' in error_lines):
            print('Tried at {}, but error in reconciliation process found'.format(times)) 
        else:
            main(nsdl_aeps,i)
            
usage_date = d.today()
os.remove('/home/sdlreco/crons/nsdl_aeps/usage/check_usage-'+str(usage_date)+'.lck')
print('File Deleted for check usage\n')
        

