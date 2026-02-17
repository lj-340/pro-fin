from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime as dt
import pageIndex.views as views
import pageIndex.industryprocss as industryprocss
import numpy as np
import pandas as pd
import fu_t1.MyTT as MyTT
import backtrader as bt
import tushare as ts
import os
tushare_token = os.environ.get('TUSHARE_TOKEN')
if tushare_token:
     ts.set_token(tushare_token)
     pro = ts.pro_api()
else:
     pro = None


class HaveCodeInfos(object):
     def __init__(self,msg=''):
        print('获取'+msg+'信息')

     def havedata_fromtu(self, sharecode='',startdate='', enddate='',inforatio=2):
          
          if enddate=='':
               enddate=dt.datetime.now()
               enddate = enddate.strftime("%Y%m%d")
          else:
               enddate = dt.datetime.strptime(enddate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if startdate=='':
               startdate=dt.datetime.strptime(enddate, "%Y%m%d").date()-dt.timedelta(days=inforatio*365)
               startdate = startdate.strftime("%Y%m%d")
          else:
               startdate = dt.datetime.strptime(startdate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if sharecode=='':
               return pd.DataFrame()
          if str.startswith(sharecode, '6'):
               sharecode = sharecode + '.SH'
          else:
               sharecode = sharecode + '.SZ'
          
          shareinfo = pro.daily(**{
                "ts_code": sharecode,
                "start_date": startdate,
                "end_date": enddate,
            }, fields=[
                "ts_code",
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "pct_chg",
                "vol",
            ])
          if shareinfo.size<=0:
               raise RuntimeError('没有找到数据')
          shareindexinfo = pro.daily_basic(**{
                "ts_code": sharecode,
                "start_date": startdate,
                "end_date": enddate,
            }, fields=[
                "ts_code",
                "trade_date",
                "turnover_rate_f",
                "volume_ratio",
                "pe_ttm",
                "pb",
                "ps_ttm",
                "dv_ttm",
                "total_share",
                "float_share",
                "free_share",
                "total_mv",
                "circ_mv"
            ])
          
          shareinfo = shareinfo.merge(shareindexinfo, how='left', left_on=["ts_code", "trade_date"],
                                        right_on=["ts_code", "trade_date"])
          shareinfo = shareinfo[[
                
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "pct_chg",
                "vol",
                "turnover_rate_f",
                "volume_ratio",
                "pe_ttm",
                "pb",
                "ps_ttm",
                "dv_ttm",
                "total_share",
               
                "free_share",
                "total_mv",
                "circ_mv"
            ]]
          
          
         # 沪深300
          indexinfo_pd= pro.index_daily(**{
                "ts_code": '000300.SH',
                "start_date": startdate,
                "end_date": enddate,
            }, fields=[
                "ts_code",
                "trade_date",
                "pct_chg",
               
            ])
          HS300=indexinfo_pd.rename(columns={'pct_chg':'HS300_Return'})
          shareinfo = shareinfo.merge(HS300[["trade_date",'HS300_Return']], how='left', left_on="trade_date",
                                        right_on="trade_date")
          
          
          # 中证500
          indexinfo_pd=  pro.index_daily(**{
                "ts_code": '000905.SH',
                "start_date": startdate,
                "end_date": enddate,
            }, fields=[
                "ts_code",
                "trade_date",
                "pct_chg",
               
            ])
          # 
          ZZ500=indexinfo_pd.rename(columns={'pct_chg':'ZZ500_Return'})
          shareinfo = shareinfo.merge(ZZ500[["trade_date",'ZZ500_Return']], how='left', left_on="trade_date",
                                        right_on="trade_date")
          # 得到每日筹码分布数据
          cost_cols=["trade_date",
                         "cost_5pct",
                         "cost_15pct",
                         "cost_50pct",
                         "cost_85pct",
                         "cost_95pct",
                         "weight_avg",]
          cost_pd=pd.DataFrame(columns=cost_cols,index=shareinfo.index)
          try:
               cost_pd= pro.cyq_perf(**{
                    "ts_code": sharecode,
                    "start_date": startdate,
                    "end_date": enddate,
               }, fields=[
                    
                         "trade_date",
                         "cost_5pct",
                         "cost_15pct",
                         "cost_50pct",
                         "cost_85pct",
                         "cost_95pct",
                         "weight_avg",
                    
               ])
          
          except Exception as e:
               cost_pd.loc[:,:]=0
               cost_pd.loc[:,'trade_date']=shareinfo['trade_date']
               
          
           

          shareinfo = shareinfo.merge(cost_pd, how='left', left_on= "trade_date",
                                                  right_on="trade_date")
          shareinfo = shareinfo.sort_values(by=['trade_date'],ascending=True)  
          for inx in shareinfo.index:
               shareinfo.loc[inx,'trade_date'] = dt.datetime.strptime(shareinfo.loc[inx,'trade_date'], '%Y%m%d').date().strftime('%Y-%m-%d')
          shareinfo.index = shareinfo['trade_date']
          shareinfo["pct_chg"]=shareinfo["pct_chg"].astype(float)
          shareinfo["high"]=shareinfo["high"].astype(float)
          shareinfo["close"]=shareinfo["close"].astype(float)
          shareinfo["HS300_Return"]=shareinfo["HS300_Return"].astype(float)
          shareinfo["ZZ500_Return"]=shareinfo["ZZ500_Return"].astype(float)
              
          shareinfo['cum_return']=np.around(((shareinfo["pct_chg"]*0.01+1).cumprod()-1)*100,5)

          shareinfo['price_change']=(np.round((shareinfo["high"]-shareinfo["close"])/shareinfo["close"],5))*100

          
          shareinfo['HS300_cum_return']=np.around(((shareinfo["HS300_Return"]*0.01+1).cumprod()-1)*100,5)
          
          shareinfo['ZZ500_cum_return']=np.around(((shareinfo["ZZ500_Return"]*0.01+1).cumprod()-1)*100,5)
          
          shareinfo = shareinfo.rename(columns={"trade_date": "datetime",
                                                  "vol": "volume",
                                                  "turnover_rate_f": "turnover",
                                                  "pe_ttm": "pe",
                                                  "pb": "pb",
                                                  "ps_ttm": "ps",
                                                  "dv_ttm": "dv",
                                                  
                                                  })
         
          # shareinfo["pct_chg"]=shareinfo["pct_chg"]*100
          shareinfo = shareinfo.fillna(0)
          

          return shareinfo

    
     def haveMACDdata(self,short=12, long=26, m=9, useingdata=pd.Series()):
          # 需要close数据
          pricedata=pd.Series()
          if useingdata.size==0:
             return pd.DataFrame()
          pricedata=useingdata
          close=pricedata.values
          columns = ['diff', 'dea','macd']
         
          # result_pd = pd.DataFrame(columns=columns, index=pricedata.index[maxperiod:-1])
         
          diff, dea, macd = MyTT.MACD(CLOSE=close,SHORT=short,LONG=long,M=m)
          macd_pd=pd.DataFrame(columns=columns, index=pricedata.index)
          macd_pd.loc[:,'diff']=diff
          macd_pd.loc[:,'dea']=dea
          macd_pd.loc[:,'macd']=macd
          return macd_pd
     
     def haveBOlldata(self, timeperiod=5,S=2,useingdata=pd.Series()):        
          close=[]
          dataindex=[]
          if useingdata.size==0:
               return pd.DataFrame()
          close=useingdata.values
          dataindex=useingdata.index
          columns=['upperband','middleband','lowerband']
          upperband, middleband, lowerband = MyTT.BOLL(CLOSE=close,N=timeperiod,P=S)
          boll_pd=pd.DataFrame(columns=columns, index=dataindex)
          boll_pd.loc[:,'upperband']=upperband
          boll_pd.loc[:,'middleband']=middleband
          boll_pd.loc[:,'lowerband']=lowerband
          return boll_pd
    
     def haveRSIdata(self,minperiod=5, maxperiod=20,useingdata=pd.Series()): 
          close=[]
          dataindex=[]
          if len(useingdata)==0:
                    return pd.DataFrame()
          close=useingdata.values
          dataindex=useingdata.index
          columns=['rsi5','rsi20']
         
          rsiArray_min = MyTT.RSI(close,minperiod)
          rsiArray_max = MyTT.RSI(close,maxperiod)
         
          rsi_pd=pd.DataFrame(columns=columns, index=dataindex)
          rsi_pd.loc[:,'rsi5']=rsiArray_min
          rsi_pd.loc[:,'rsi20']=rsiArray_max
          return rsi_pd
       
     def haveKDJdata(self,useingdata=pd.DataFrame(),N=9, M1=3, M2=3,):
          if useingdata.size==0:
               return pd.DataFrame()
          pricedata =useingdata
          dataindex =  useingdata.index

          high = pricedata['high'].values
          low = pricedata['low'].values
          close=pricedata['close'].values
          columns = ['K', 'D', 'J']
          result = pd.DataFrame(columns=columns, index=pricedata['close'].index)
          result.loc[:, :] = 0
          K,D,J = MyTT.KDJ(CLOSE=close,HIGH=high,LOW=low,N=N,M1=M1,M2=M2)
          
          kdj_pd=pd.DataFrame(columns=columns, index=dataindex)
          kdj_pd.loc[:,'K']=K
          kdj_pd.loc[:,'D']=D
          kdj_pd.loc[:,'J']=J
          return kdj_pd
     def haveBIASdata(self,useingdata=pd.Series(),L1=5, L2=10, L3=20,):
          close=[]
          dataindex=[]
          if len(useingdata)==0:
               return pd.DataFrame()
          close=useingdata.values
          dataindex=useingdata.index
          columns=['Bias5','Bias10','Bias20']

          Bias5,Bias10,Bias20 = MyTT.BIAS(close,L1, L2, L3)
       
          bias_pd=pd.DataFrame(columns=columns, index=dataindex)
          bias_pd.loc[:,'Bias5']=Bias5
          bias_pd.loc[:,'Bias10']=Bias10
          bias_pd.loc[:,'Bias20']=Bias20
          return bias_pd
           
     def havebasicdata_fromtu(self,sharecode='',startdate='', enddate=''):
          if enddate=='':
               enddate=dt.datetime.now()
               enddate = enddate.strftime("%Y%m%d")
          else:
               enddate = dt.datetime.strptime(enddate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if startdate=='':
               startdate=dt.datetime.strptime(enddate, "%Y%m%d").date()-dt.timedelta(days=2*365)
               startdate = startdate.strftime("%Y%m%d")
          else:
               startdate = dt.datetime.strptime(startdate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if sharecode=='':
               return pd.DataFrame()
          if str.startswith(sharecode, '6'):
               sharecode = sharecode + '.SH'
          else:
               sharecode = sharecode + '.SZ'
          sharebasicinfo_pd = pro.stock_basic(**{
               "ts_code": sharecode,
               }, fields=[
               "ts_code",
               "name", # 股票名称
               "area", # 地域
               "industry", # 行业
               "list_date", # 上市时间
               "fullname", # 股票全称
               "is_hs" # 是不是港股通
               ])
          df = pro.stock_company(**{
               "ts_code": sharecode,
               }, fields=[
               "ts_code",
               "city", # 城市
               "employees",# 雇员数量
               "main_business"# 主要业务
               ])
          sharebasicinfo_pd=sharebasicinfo_pd.merge(df,how='inner',left_on='ts_code',right_on='ts_code')
          # 得到部分财务指标情况
          df = pro.fina_indicator(**{
               "ts_code":sharecode,
               "ann_date": "",
               "start_date": startdate,
               "end_date": enddate,
               }, fields=[
               "ts_code",
               "ann_date", # 上报时间
               "eps", # 每股收益
               "ebit_ps", # 每股息税前利润
               "roe", # 净资产收益率
               'total_revenue_ps',# 每股营业收入
               "debt_to_assets", # 资产负债率
               "ebitda_to_debt", # 息税折旧摊销前利润/负债合计
               "q_profit_qoq", # 净利润环比增长率(%)(单季度
               "q_profit_yoy", # 净利润同比增长率(%)(单季度)
               "rd_exp", # 研发费用
               "bps", # 每股净资产
               "roic", # 投入资本回报率
               "basic_eps_yoy" # 基本每股收益同比增长率(%)
               ])
          df=df.sort_values(by="ann_date",ascending=False)
          df_head=df.head(1)
          sharebasicinfo_pd=sharebasicinfo_pd.merge(df_head,how='inner',left_on='ts_code',right_on='ts_code')
          # 获取总资产和净资产
          asset_cols=[ 
                    "trade_date",# 
                    "ts_code",
                    "total_assets",# 总资产
                    "liquid_assets", # 流动资产
                    
                    "holder_num" # 股东人数
                    ]
          df=pd.DataFrame(columns=asset_cols)
          try:
               df = pro.bak_basic(**{
               "ts_code": sharecode,
               }, fields=[
               "trade_date",# 
               "ts_code",
               "total_assets",# 总资产
               "liquid_assets", # 流动资产
               
               "holder_num" # 股东人数
               ])
               df=df.sort_values(by="trade_date",ascending=False)
              
          except Exception as e:
               df.loc[0,:]=0
               df.loc[0,"ts_code"]=sharecode
          df_head=df.head(1)
          sharebasicinfo_pd=sharebasicinfo_pd.merge(df_head,how='inner',left_on='ts_code',right_on='ts_code')
          return sharebasicinfo_pd
          
     # 得到股票所属的概念,按照东方财富数据获取
     def havecodeconcept_data(self,sharecode=''):
          if sharecode=='':
               return []
          concept_check=industryprocss.industryprocess()
          conceptlist =concept_check.have_em_concept_name()
          haveconcept=[]
          for conceptname in conceptlist:
               concelist=concept_check.have_em_concept_list(conceptname)
               if sharecode in concelist:
                    haveconcept.append(conceptname)
          return haveconcept
               

     # 得到股票的主营构成
     def havecodesales_data(self,sharecode='',startdate='',enddate=''):
          if enddate=='':
               enddate=dt.datetime.now()
               enddate = enddate.strftime("%Y%m%d")
          else:
               enddate = dt.datetime.strptime(enddate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if startdate=='':
               startdate=dt.datetime.strptime(enddate, "%Y%m%d").date()-dt.timedelta(days=2*365)
               startdate = startdate.strftime("%Y%m%d")
          else:
               startdate = dt.datetime.strptime(startdate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if sharecode=='':
               return pd.DataFrame()
          if str.startswith(sharecode, '6'):
               sharecode = sharecode + '.SH'
          else:
               sharecode = sharecode + '.SZ'
          sales_pd = pro.fina_mainbz(**{
               "ts_code": sharecode,
               "start_date": startdate,
               "end_date":enddate,
               }, fields=[
               "ts_code",
               "end_date",
               "bz_item", #项目
               "bz_sales",#收入总额
               "bz_profit",
               "bz_cost",
               "curr_type"
               ])
         
          sales_pd=sales_pd.sort_values(by="end_date",ascending=False)
          new_sales_pd=pd.DataFrame(columns=sales_pd.columns)
          top_date=str(sales_pd.head(1)["end_date"].values[0])
          for index in sales_pd.index:
               curr_endate=str(sales_pd.loc[index,'end_date'])
               if curr_endate==top_date:
                    temp_pd=pd.DataFrame([sales_pd.loc[index,:].values],columns=sales_pd.loc[index,:].index)
                  
                    new_sales_pd=pd.concat([new_sales_pd,temp_pd]) 

          new_sales_pd=new_sales_pd.dropna()
          new_sales_pd=new_sales_pd.drop_duplicates(subset="bz_item",keep='first')
          new_sales_pd["bz_profit"]=new_sales_pd["bz_profit"].astype(float)
          new_sales_pd["bz_cost"]=new_sales_pd["bz_cost"].astype(float)
          
          new_sales_pd['sales_item_ratio']=np.round(new_sales_pd["bz_profit"].div(new_sales_pd["bz_cost"],fill_value=0),5)*100
          
          
          # new_sales_pd["bz_profit"]=new_sales_pd["bz_profit"].astype(str)
          # new_sales_pd["bz_cost"]=new_sales_pd["bz_cost"].astype(str)
          # new_sales_pd['sales_item_ratio']=new_sales_pd['sales_item_ratio'].astype(str)
          new_sales_pd=new_sales_pd[[
                                   "ts_code", 
                                   "end_date",
                                   "bz_item", #项目
                                   "bz_sales", #收入总额
                                   'sales_item_ratio' #项目盈利能力
                                   ]]
          
          return new_sales_pd

     # 得到股票的十大流通股东
     def havecodeholeder_data(self,sharecode='',startdate='',enddate=''):
          if enddate=='':
               enddate=dt.datetime.now()
               enddate = enddate.strftime("%Y%m%d")
          else:
               enddate = dt.datetime.strptime(enddate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if startdate=='':
               startdate=dt.datetime.strptime(enddate, "%Y%m%d").date()-dt.timedelta(days=2*365)
               startdate = startdate.strftime("%Y%m%d")
          else:
               startdate = dt.datetime.strptime(startdate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if sharecode=='':
               return pd.DataFrame()
          if str.startswith(sharecode, '6'):
               sharecode = sharecode + '.SH'
          else:
               sharecode = sharecode + '.SZ'
          # 得到十大流通股东
          holder_pd = pro.top10_floatholders(**{
               "ts_code": sharecode,
               "start_date": startdate,
               "end_date": enddate,
               }, fields=[
               "ts_code",
               "ann_date",
               "end_date",
               "holder_name",
               "hold_amount"
               ])
          holder_pd=holder_pd.sort_values(by="ann_date",ascending=False)
          new_holder_pd=pd.DataFrame()
          top_date=str(holder_pd.head(1)["ann_date"].values[0])
          for index in holder_pd.index:
               curr_endate=str(holder_pd.loc[index,'ann_date'])
               if curr_endate==top_date:
                    temp_pd=pd.DataFrame([holder_pd.loc[index,:].values],columns=holder_pd.loc[index,:].index)
                    new_holder_pd=pd.concat([new_holder_pd,temp_pd]) 
          new_holder_pd=new_holder_pd.dropna()
          new_holder_pd=new_holder_pd.drop_duplicates(subset="holder_name",keep='first')
          return new_holder_pd

     def updateMultiShareData_fromTU(self,multticodes=[],opendate='',closedate=''):
        multishares = multticodes
        if len(multishares)==0:
                return '需要处理的股票代码'
        opendate = dt.datetime.strptime(opendate, '%Y-%m-%d').date().strftime("%Y%m%d")
        closedate = dt.datetime.strptime(closedate, '%Y-%m-%d').date().strftime("%Y%m%d")
        dateArray=pd.date_range(start=opendate,end=closedate,freq='D')
        columns=['datetime','return']
        multisharePD = pd.DataFrame(columns=columns)
        for tradedate in dateArray:
            tradedate =tradedate.strftime("%Y%m%d")
            #  筛选后再首先获得行情数据
            print(str(tradedate)+':读取')
            havecodeinfo = pro.daily(**
                                     {
                                      "trade_date": tradedate,
                                      },
                                     fields=["ts_code",
                                             "trade_date",
                                             "pct_chg",  # 当天的收益
                                             "vol"
                                             ]
                                     )
            if havecodeinfo.size==0:
                print(str(tradedate)+':没有数据')
                continue
            all_df_daily = pro.daily_basic(**{
                "trade_date": tradedate,
            }, fields=[
                "ts_code",
                "trade_date",
               
                "circ_mv" # 流通市值
            ])

            havecodeinfo = havecodeinfo.merge(all_df_daily, how='inner', left_on=["ts_code", "trade_date"],
                                              right_on=["ts_code", "trade_date"])
            havecodeinfo= havecodeinfo.rename(columns={'pct_chg':'return'})
            havecodeinfo.index = havecodeinfo['trade_date']
          #   havecodeinfo = havecodeinfo.drop(columns=['trade_date'])
            share_codes=havecodeinfo['ts_code'].values
            haveweightdatapd=pd.DataFrame()
            for sharecode in share_codes:
                if str(sharecode)[0:6] in multishares:
                    if haveweightdatapd.size==0:
                        haveweightdatapd=havecodeinfo[havecodeinfo['ts_code']==sharecode]
                    else:
                        haveweightdatapd =pd.concat([haveweightdatapd,havecodeinfo[havecodeinfo['ts_code'] == sharecode]])

            havetemppd=self.multiWeighted(dataPD=haveweightdatapd,columns=columns)
            if multisharePD.size==0:
                multisharePD=havetemppd
            else:
                multisharePD=pd.concat([multisharePD,havetemppd])
            print(str(tradedate)+':读取成功！')
     #    multisharePD['return']=multisharePD.astype({"return": 'float'})
        multisharePD["return"]=multisharePD["return"].astype(float)
        multisharePD['cum_return']=((multisharePD["return"]*0.01+1).cumprod()-1).mul(100.0)
        
        multisharePD = multisharePD.sort_values(by=['datetime'],ascending=True) 
        multisharePD.index=multisharePD['datetime'].values 
        for inx in multisharePD.index:
               multisharePD.loc[inx,'datetime'] = dt.datetime.strptime(multisharePD.loc[inx,'datetime'], '%Y%m%d').date().strftime('%Y-%m-%d')
        multisharePD.index=multisharePD['datetime'].values
        return multisharePD

     def multiWeighted(self,columns=['datetime','return'], dataPD=pd.DataFrame(),usecols='return',weitghnames='circ_mv') -> pd.DataFrame:
          
         
          ret_pd = pd.DataFrame(columns=columns)
         
          totalliquidvalue = dataPD[weitghnames].values.sum()
          weightbyliquid = (dataPD[usecols].mul(dataPD[weitghnames]) / totalliquidvalue).sum()
          ret_pd.loc[0, 'return'] = np.round(weightbyliquid, 5)
          ret_pd.loc[0, 'datetime']=dataPD['trade_date'].values[0]
                   
          return ret_pd
     def haveMultiValueData_fromTU(self,multticodes=[],startdate='',enddate='',inforatio=1):
          multishares = multticodes
          if len(multishares)==0:
                raise RuntimeError('需要处理的股票代码')
          if enddate=='':
               enddate=dt.datetime.now()
               enddate = enddate.strftime("%Y%m%d")
          else:
               enddate = dt.datetime.strptime(enddate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if startdate=='':
               startdate=dt.datetime.strptime(enddate, "%Y%m%d").date()-dt.timedelta(days=inforatio*365)
               startdate = startdate.strftime("%Y%m%d")
          else:
               startdate = dt.datetime.strptime(startdate, '%Y-%m-%d').date().strftime("%Y%m%d")
          
          opendate = dt.datetime.strptime(startdate, "%Y%m%d")
          closedate = dt.datetime.strptime(enddate, "%Y%m%d")
          dateArray=pd.date_range(start=opendate,end=closedate,freq='D')
          cols=['datetime','m_pe','m_ps','m_b','m_mv']
          multi_mean=pd.DataFrame(columns=cols)
          for tradedate in dateArray:
            tradedate =tradedate.strftime("%Y%m%d")
            #  筛选后再首先获得行情数据
            print(str(tradedate)+':读取')
            shareindexinfo = pro.daily_basic(**{
                "trade_date": tradedate,
            }, fields=[
                "ts_code",
                "trade_date",
                "pe_ttm",
                "pb",
                "ps_ttm",
                "total_mv",
            ])
            if shareindexinfo.size==0:
                print(str(tradedate)+':没有数据')
                continue
            share_codes=shareindexinfo['ts_code'].values
            havesamecodepd=pd.DataFrame()
            for sharecode in share_codes:
                if str(sharecode)[0:6] in multishares:
                    if havesamecodepd.size==0:
                        havesamecodepd=shareindexinfo[shareindexinfo['ts_code']==sharecode]
                    else:
                        havesamecodepd =pd.concat([havesamecodepd,shareindexinfo[shareindexinfo['ts_code']==sharecode]])

            temp_pd=pd.DataFrame(columns=cols)
            temp_pd.loc[0,cols[0]]=tradedate
            temp_pd.loc[0,cols[1]]=str(np.around(havesamecodepd["pe_ttm"].mean(axis=0),5))
            temp_pd.loc[0,cols[2]]=str(np.around(havesamecodepd["pb"].mean(axis=0),5))
            temp_pd.loc[0,cols[3]]=str(np.around(havesamecodepd["ps_ttm"].mean(axis=0),5))
            temp_pd.loc[0,cols[4]]=havesamecodepd["total_mv"].mean(axis=0)
            if multi_mean.size==0:
                multi_mean=temp_pd
            else:
                multi_mean=pd.concat([multi_mean,temp_pd])
            print(str(tradedate)+':读取成功')
          multi_mean = multi_mean.sort_values(by=['datetime'],ascending=True) 
          multi_mean.index=multi_mean['datetime'].values 
          for inx in multi_mean.index:
               multi_mean.loc[inx,'datetime'] = dt.datetime.strptime(multi_mean.loc[inx,'datetime'], '%Y%m%d').date().strftime('%Y-%m-%d')
          multi_mean['m_mv']=np.around((multi_mean['m_mv'].astype(float))*1e-4,3)
          multi_mean['m_mv']=multi_mean['m_mv'].astype(str)
          return multi_mean
     def havesinglevaluedata_fromtu(self, sharecode='',startdate='', enddate='',inforatio=2): 
          if enddate=='':
               enddate=dt.datetime.now()
               enddate = enddate.strftime("%Y%m%d")
          else:
               enddate = dt.datetime.strptime(enddate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if startdate=='':
               startdate=dt.datetime.strptime(enddate, "%Y%m%d").date()-dt.timedelta(days=inforatio*365)
               startdate = startdate.strftime("%Y%m%d")
          else:
               startdate = dt.datetime.strptime(startdate, '%Y-%m-%d').date().strftime("%Y%m%d")
          if sharecode=='':
               return pd.DataFrame()
          if str.startswith(sharecode, '6'):
               sharecode = sharecode + '.SH'
          else:
               sharecode = sharecode + '.SZ'
          shareindexinfo = pro.daily_basic(**{
                "ts_code": sharecode,
                "start_date": startdate,
                "end_date": enddate,
            }, fields=[
                "ts_code",
                "trade_date",
                "pe_ttm",
                "pb",
                "ps_ttm",
               
                "total_mv",
            ])
          shareindexinfo=shareindexinfo.rename(columns={"trade_date":'datetime',
                                                       'pe_ttm':'pe',"ps_ttm":'ps','total_mv':'mv'})
          shareindexinfo.index=shareindexinfo['datetime'].values 
          shareindexinfo['mv']=np.around((shareindexinfo['mv'].astype(float))*1e-4,3)
          shareindexinfo['mv']=shareindexinfo['mv'].astype(str)
          shareindexinfo = shareindexinfo.sort_values(by=['datetime'],ascending=True) 
          for inx in shareindexinfo.index:
                   shareindexinfo.loc[inx,'datetime'] = dt.datetime.strptime(shareindexinfo.loc[inx,'datetime'], '%Y%m%d').date().strftime('%Y-%m-%d')
          return shareindexinfo



     