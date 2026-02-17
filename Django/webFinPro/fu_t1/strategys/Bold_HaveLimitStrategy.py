from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import pandas as pd

import numpy as np
import datetime as dt
import math
import tushare as ts
import os
from django.conf import settings
import pageIndex.views as views

# Load tushare token from environment variable (TUSHARE_TOKEN)
tushare_token = os.environ.get('TUSHARE_TOKEN')
if tushare_token:
    ts.set_token(tushare_token)
    pro = ts.pro_api()
else:
    pro = None
import pageIndex.views as views


class Bold_HaveLimitStrategy(bt.Strategy):
    params = (
        ('period', 5),
        ('printlog', True),
        ('seltype',1),
         ('baseindex',"000001.SH"),
        ('username',"bochuan"),
        ('tragename',"Bold_HaveLimitStrategy"),
        ('save_sharecodetype',""),
    )
    def savesel_codes(self):
        try:
            
            if self.myfile_forsaveselcodes.size>0:
                filepath=settings.BASE_DIR+"/static/download/"+self.p.username+'/'
                nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                filename=self.p.tragename+str(nowtime)+'.csv'
                cols=self.myfile_forsaveselcodes.columns
                shareconditionsdict,strongconditondict=views.havebacktradeconditions()
                conkeys=self.__conditiondict.keys()
                str_con=' '
                for currkey in conkeys:
                    namevalue= shareconditionsdict[currkey]
                    str_con=str_con+str(namevalue)+':'+str(self.__conditiondict[currkey])+'|\n'
                str_strong=' '
                strkeys=self.__strongcondition.keys()
                for currkey in strkeys:
                    if str(currkey)=='longMin':
                        
                        if  len(self.__strongcondition[currkey].keys())>0:
                            perioddays=self.__strongcondition[currkey]['period']
                            
                            mingain=self.__strongcondition[currkey]['gain']
                            str_strong=str_strong+'连续增长|'+'周期:'+str(perioddays)+'幅度:'+str(mingain)+'\n'
                    elif str(currkey)=='totalRet': 
                        if  len(self.__strongcondition[currkey].keys())>0:
                            perioddays=self.__strongcondition[currkey]['period']
                            
                            mingain=self.__strongcondition[currkey]['gain']
                            str_strong=str_strong+'短期涨幅|'+'周期:'+str(perioddays)+'幅度:'+str(mingain)+'\n'
                str_tech=' '
                havallteckconditions =views.havefigureindexconditions()
                tech_con=self.__teckindexcondict
                techkeys=tech_con.keys()
                for currkey in techkeys:
                    namevalue=havallteckconditions[currkey][0]
                    str_tech=str_tech+str(namevalue)+':'+str(tech_con[currkey])+'|\n'
                self.myfile_forsaveselcodes.loc[:,cols[3]]=str_con
                self.myfile_forsaveselcodes.loc[:,cols[4]]=str_strong
                self.myfile_forsaveselcodes.loc[:,cols[5]]=str_tech
                self.myfile_forsaveselcodes.loc[:,cols[6]]=self.p.save_sharecodetype
                self.myfile_forsaveselcodes.to_csv(filepath+filename,encoding='GBK',index=False)
        except Exception as e:
            print(e)
            print('savefile')
  
    def havestrongsharecode(self, codelist, tradedate='',strongcondition={'longMin': dict(), 'totalRet': dict()}):
        longMin_list=[]
        totalRet_list=[]
        haveconditions = strongcondition.keys()
        for condition_key in haveconditions:
            # 筛选连涨天数股票
            if len(strongcondition[condition_key].keys())==0:
                continue
            if condition_key == 'longMin':
                perioddays=strongcondition[condition_key]['period']
                mingain=strongcondition[condition_key]['gain']
                for code_keys in codelist:
                    try:
                        data=self.getdatabyname(code_keys)
                        ##连续增长时长
                        #(np.array(returns_pd['return'].tolist())==0).all(
                        pct_list=[data.pct_chg[i] for i in range(-perioddays+1,1,1)]
                        istimeok= (np.array(pct_list)>0).all()
                      
                        ##连续增长幅度
                        isupok=((pd.Series(pct_list)*0.01+1).cumprod()-1).to_list()[-1]>mingain
                    
                        if istimeok and isupok:
                            longMin_list.append(code_keys)
                    except Exception as e:
                        print(str(code_keys) + '处理报错!')
                        print(e)
                        continue
               
            elif condition_key == 'totalRet':
                perioddays = strongcondition[condition_key]['period']
                mingain = strongcondition[condition_key]['gain']
                for code_keys in codelist:
                    try:
                       data=self.getdatabyname(code_keys)
                       pct_list=[data.pct_chg[i] for i in range(-perioddays+1,1,1)] 
                       isupok=((pd.Series(pct_list)*0.01+1).cumprod()-1).to_list()[-1]>mingain
                   
                       if isupok:
                            totalRet_list.append(code_keys)
                    except Exception as e:
                        print(str(code_keys) + '处理报错！')
                        print(e)
                        continue
          
        return np.union1d(longMin_list,totalRet_list)
  
    def haveallsharebyconditions_singleday(self, codelist, conditiondict=dict()):
        
        import fu_t1 as fu_t1
        conditions = conditiondict
        if len(conditions.values()) == 0:
            print('没有设置条件!')
            return
        # 首先对上市公司股票进行剔除,默认：1.剔除非正常交易的股票。2.在指定时间内均有值得股票。3.剔除掉B股数据
        # codelist = self.cleanshare(codelist=codelist, startdate=startdate, enddate=enddate, isbalance=False)
        # codelist = tuple(codelist)
        return_list=[]
        conkeys = conditions.keys()
        for conkey in conkeys:
            if (str(conkey) == 'volume'):
                volumnRange = conditions[conkey]

                # 只有在这种条件下才检测条件 条件的上限和下限都大于0，且下限小于上限
                
                if not ((np.equal(volumnRange, 0).all()) or (volumnRange[0] >= volumnRange[1])):
                    curr_list=[]
                    vol_min=volumnRange[0]
                    vol_max=volumnRange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        if (data.volume[0] >=vol_min) and (data.volume[0] <=vol_max):
                               curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            elif (str(conkey) == 'cumReturn'):
                # 取累计收益率条件,用的是累计，而不是平均
                returnrange = conditions[conkey]

                if not ((np.equal(returnrange, 0).all()) or (returnrange[0] >= returnrange[1])):
                    curr_list=[]
                    min_value=returnrange[0]
                    max_value=returnrange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)

                        if (data.pct_chg[0] >=min_value) and (data.pct_chg[0] <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            elif (str(conkey) == 'pe'):
                # 取pe条件
                perange = conditions[conkey]
                if not ((np.equal(perange, 0).all()) or (perange[0] >= perange[1])):
                    curr_list=[]
                    min_value=perange[0]
                    max_value=perange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)

                        if (data.pe_ttm[0] >=min_value) and (data.pe_ttm[0] <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            elif (str(conkey) == 'marketvalue'):

                # 取市值条件
                valuerange = conditions[conkey]
                if not ((np.equal(valuerange, 0).all()) or (valuerange[0] >= valuerange[1])):
                    curr_list=[]
                    min_value=valuerange[0]
                    max_value=valuerange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        if (data.marketvalue[0] >=min_value) and (data.marketvalue[0] <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            elif (str(conkey) == 'ps'):
                # 取ps条件
                psrange = conditions[conkey]
                if not ((np.equal(psrange, 0).all()) or (psrange[0] >= psrange[1])):
                    curr_list=[]
                    min_value=psrange[0]
                    max_value=psrange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        if (data.ps_ttm[0] >=min_value) and (data.ps_ttm[0] <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            
            elif (str(conkey) == 'pb'):
                # 取pb条件
                pbrange = conditions[conkey]
                if not ((np.equal(pbrange, 0).all()) or (pbrange[0] >= pbrange[1])):
                    curr_list=[]
                    min_value=pbrange[0]
                    max_value=pbrange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        if (data.pb[0] >=min_value) and (data.pb[0] <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            elif (str(conkey) == 'turnover'):
                # 取换手率条件，数值在另一张表中
                turnrange = conditions[conkey]
                if not ((np.equal(turnrange, 0).all()) or (turnrange[0] >= turnrange[1])):
                    curr_list=[]
                    min_value=turnrange[0]
                    max_value=turnrange[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        if (data.turnover_rate[0] >=min_value) and (data.turnover_rate[0] <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            
            elif str(conkey) == 'price_change_ratio':
                pcg_range = conditions[conkey]
                if not ((np.equal(pcg_range, 0).all()) or (pcg_range[0] >= pcg_range[1])):
                    curr_list=[]
                    min_value=pcg_range[0]
                    max_value=pcg_range[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        p_change=(np.log(data.high[0])-np.log(data.low[0]))*100
                        if (p_change >=min_value) and (p_change <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)   
            # 交易量变化
            elif (str(conkey) == 'vol_change'):
                vol_range = conditions[conkey]
                # 只有在这种条件下才检测条件 条件的上限和下限都大于0，且下限小于上限
                if not ((np.equal(vol_range, 0).all()) or (vol_range[0] >= vol_range[1])):
                    curr_list=[]
                    min_value=vol_range[0]
                    max_value=vol_range[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        vol_mean=np.array([data.volume[i] for i in range(-5,0,1)]).mean()
                        vol_change=(np.log(data.volume[0])-np.log(vol_mean))*100
                        if (vol_change >=min_value) and (vol_change <=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            # 换手率变化
            elif (str(conkey) == 'turnover_ratio'):
                turn_range = conditions[conkey]
                # 只有在这种条件下才检测条件 条件的上限和下限都大于0，且下限小于上限
                if not ((np.equal(turn_range, 0).all()) or (turn_range[0] >= turn_range[1])):
                    curr_list=[]
                    min_value=turn_range[0]
                    max_value=turn_range[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        turn_mean=np.array([data.turnover_rate[i] for i in range(-5,0,1)]).mean()
                        t_change=(np.log(data.turnover_rate[0])-np.log(turn_mean))*100
                        if (t_change>=min_value) and (t_change<=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
            # 量比
            elif (str(conkey) == 'volume_ratio'):
                volumeRange = conditions[conkey]
                if not ((np.equal(volumeRange, 0).all()) or (volumeRange[0] >= volumeRange[1])):
                    curr_list=[]
                    min_value=turn_range[0]
                    max_value=turn_range[1]
                    for code in codelist:
                        data=self.getdatabyname(code)
                        if (data.volume_ratio[0]>=min_value) and (data.volume_ratio[0]<=max_value):
                            curr_list.append(code) 
                    if len(return_list)==0:
                        return_list=curr_list
                    else:
                        return_list=np.intersect1d(return_list,curr_list)
        
        return return_list
    def havesharelistbytech(self, codelist, teckdict=dict()):
        if len(teckdict.keys())<=0:
               return
        havallteckconditions =views.havefigureindexconditions()
          
        for conkey in teckdict.keys():
                if conkey == 'RSI':
                    strcon = teckdict[conkey]
                    buysignal = 70
                    sellsignal = 30
                    P1 = 6
                    
                    if strcon == '':
                        buysignal = havallteckconditions[conkey][1]['buysignal']
                        sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        P1= havallteckconditions[conkey][1]['P1']
                    else:
                        try:
                            buysignal = strcon['buysignal']
                        except:
                            buysignal = havallteckconditions[conkey][1]['buysignal']
                            continue
                        try:
                            sellsignal = strcon['sellsignal']
                        except:
                            sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        try:
                            P1 = strcon['P1']
                        except:
                            P1 = havallteckconditions[conkey][1]['P1']
                      
                    
                    self.Rsindicator_dict = dict()
                   
                    for data in self.datas:
                        try:
                            self.Rsindicator_dict[data._name] = bt.indicators.RelativeStrengthIndex(data.close, period=P1,safediv=True).rsi -buysignal
                        except:
                            print(data._name+'错误')
                            continue
                 
                  
                elif conkey == 'MACD':
                    strcon = teckdict[conkey]
                    buysignal = 0
                    sellsignal = 0
                    short = 12
                    long = 26
                    mid = 9
                    
                    if strcon == '':
                        buysignal = havallteckconditions[conkey][1]['buysignal']
                        sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        short = havallteckconditions[conkey][1]['SHORT']
                        long = havallteckconditions[conkey][1]['LONG']
                        m = havallteckconditions[conkey][1]['MID']
                    else:
                        try:
                            buysignal = strcon['buysignal']
                        except:
                            buysignal = havallteckconditions[conkey][1]['buysignal']
                        try:
                            sellsignal = strcon['sellsignal']
                        except:
                            sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        try:
                            short = strcon['SHORT']
                        except:
                            short = havallteckconditions[conkey][1]['SHORT']
                        try:
                            long = strcon['LONG']
                        except:
                            long = havallteckconditions[conkey][1]['LONG']
                        try:
                            mid = strcon['MID']
                        except:
                             mid = havallteckconditions[conkey][1]['MID']
                        
                    
                    self.MACD_dict = dict()
                    for data in self.datas:
                        self.MACD_dict[data._name] = bt.indicators.MACD(data.close, 
                                                  period_me1=short,period_me2=long,period_signal=mid).signal-buysignal
                elif conkey == 'MEAN':
                    strcon = teckdict[conkey]
                    buysignal = 0
                    sellsignal = 0
                    shortperiod = 5
                    longperiod = 20

                   
                    if strcon == '':
                        sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        buysignal = havallteckconditions[conkey][1]['buysignal']
                        shortperiod = havallteckconditions[conkey][1]['SHORT']
                        longperiod = havallteckconditions[conkey][1]['LONG']

                    else:
                        try:
                            sellsignal = strcon['sellsignal']
                        except:
                            sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        try:
                            buysignal = strcon['buysignal']
                        except:
                            buysignal = havallteckconditions[conkey][1]['buysignal']
                        try:
                            shortperiod = strcon['SHORT']
                        except:
                            shortperiod = havallteckconditions[conkey][1]['SHORT']
                        try:
                            longperiod = strcon['LONG']
                        except:
                            longperiod = havallteckconditions[conkey][1]['LONG']
                    
                    self.MEAN_dict = dict()
                    for data in self.datas:
                         SMA1= bt.indicators.SmoothedMovingAverage(data.close,period=shortperiod)
                         SMA2= bt.indicators.SmoothedMovingAverage(data.close,period=longperiod)
                         self.MEAN_dict[data._name] =(SMA1-SMA2) -buysignal

                elif conkey == 'KDJ':
                    strcon = teckdict[conkey]
                    sellsignal = 0
                    buysignal = 0
                    N = 9
                    M1 = 3
                    M2 = 3

                    
                    if strcon == '':
                        sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        buysignal = havallteckconditions[conkey][1]['buysignal']
                        N = havallteckconditions[conkey][1]['N']
                        M1 = havallteckconditions[conkey][1]['M1']
                        M2 = havallteckconditions[conkey][1]['M2']

                    else:
                        try:
                            sellsignal = strcon['sellsignal']
                        except:
                            sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        try:
                            buysignal = strcon['buysignal']
                        except:
                            buysignal = havallteckconditions[conkey][1]['buysignal']
                        try:
                            N = strcon['P1']
                        except:
                            N = havallteckconditions[conkey][1]['P1']
                        try:
                            M1 = strcon['M1']
                        except:
                            M1 = havallteckconditions[conkey][1]['M1']
                        try:
                            M2 = strcon['M2']
                        except:
                            M2 = havallteckconditions[conkey][1]['M2']
                       

                    self.KDJ_dict = dict()
                    for data in self.datas:
                         # llv=data.close-bt.Min(data.low.get(ago=0,size=N))
                         data_low=np.min([data.low[i] for i in range(-N+1,1,1)])
                         data_high=np.max([data.high[i] for i in range(-N+1,1,1)])
                         llv=data.close-data_low
                         lhv=data_high-data_low
                         RSV=(llv/lhv)*100
                         K=bt.indicators.SmoothedMovingAverage(RSV,period=M1)
                         D=bt.indicators.SmoothedMovingAverage(K,period=M2)
                         J=3*K-2*D
                         self.KDJ_dict[data._name] =K-D-buysignal
                elif conkey == 'Bias':
                    strcon = teckdict[conkey]
                    sellsignal= 0
                    buysignal = 0
                    
                    L1=5
                    L2=10
                    L3=20
                    if strcon == '':
                        L1 = havallteckconditions[conkey][1]['L1']
                        sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        buysignal = havallteckconditions[conkey][1]['buysignal']


                    else:
                        try:
                            L1 = strcon['L1']
                        except:
                            L1 = havallteckconditions[conkey][1]['L1']
                        try:
                            sellsignal= strcon['sellsignal']
                        except:
                            sellsignal= havallteckconditions[conkey][1]['sellsignal']
                        try:
                            buysignal = strcon['buysignal']
                        except:
                            buysignal = havallteckconditions[conkey][1]['buysignal']
                        
                    self.Bias_dict = dict()
                    for data in self.datas:
                         avg=bt.indicators.MovingAverageSimple(data.close,period=L1)
                         bias1= (data.close-avg)
                         bias_signal=(bias1/avg)*100
                         self.Bias_dict[data._name] =bias_signal -buysignal
                    
                elif conkey == 'BOLL':
                    strcon = teckdict[conkey]
                    sellsignal= 0
                    buysignal = 0
                    P1 = 5
                    S = 2
                    
                    if strcon == '':
                        sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        buysignal = havallteckconditions[conkey][1][' buysignal']
                        P1  = havallteckconditions[conkey][1]['P1']
                        S = havallteckconditions[conkey][1]['S']
                    else:
                        try:
                            sellsignal = strcon['sellsignal']
                        except:
                            sellsignal = havallteckconditions[conkey][1]['sellsignal']
                        try:
                            buysignal = strcon['buysignal']
                        except:
                           buysignal = havallteckconditions[conkey][1]['buysignal']
                        try:
                            P1 = strcon['P1']
                        except:
                            P1  = havallteckconditions[conkey][1]['P1']
                        try:
                            S = strcon['S']
                        except:
                            S = havallteckconditions[conkey][1]['S']
                    self.BOLL_dict = dict()
                    for data in self.datas:
                        Boll_signal=bt.indicators.BollingerBands(data.close,period=P1,devfactor=S)
                        self.BOLL_dict[data._name]= buysignal-Boll_signal.bot
    
    
    __conditiondict={}
    __strongcondition={}
    __teckindexcondict={}

    @classmethod
    def set_cons(cls,conditiondict,strongcondition,teckindexcondict):
        cls.__conditiondict=conditiondict
        cls.__strongcondition=strongcondition
        cls.__teckindexcondict=teckindexcondict
    
    @classmethod
    def get_cons(cls):
       return  cls.__conditiondict,cls.__strongcondition,cls.__teckindexcondict


    __selffactors={
        'period':[5,'牛熊周期'],
        # 最大建仓数量
        'max_hold_stock_nums':[4,'最大建仓数量'],
        # 选出来的股票
        'bearpercent':[0.7,'熊市比例'],
        'threshold':[0.003,'牛熊切换阈值'],
        'startcount':[10,'启动时刻'],
        ##黄金坑参数
        'inicount':[-1,'查询起始'],
        'downgrowth':[0.1,'下探幅度'],
        'middlegrowth':[0.02,'震荡幅度'],
        'upgrowth':[0.05,'上升幅度'],
        'testperiod':[5,'测试周期'],
        'todaygrowth':[0.05,'当日幅度'],
        'meangrowth':[0.05,'均值幅度'],
        
        ##追板参数
        # 'inicount':[0,'初始查询值'],
        # 'growth':[0.5,'增长幅度'],
        'numoflimits':[2,'板上次数'],
        'chggrowth':[0.05,'调整幅度'],
        'chgturnover':[30,'换手幅度']
     }

    
    @classmethod
    def have_selffactors(cls):
        return cls.__selffactors

    @classmethod
    def set_selffactors(cls,factors={}):
        for key in  cls.__selffactors.keys():
            cls.__selffactors[key][0] =factors[key]

    #保存回测过程信息
    __btinfos=[]
    @classmethod
    def rd_bt_infos(cls):
        return cls.__btinfos
    
   
    @classmethod
    def rd_bt_infos(cls):
        return cls.__btinfos
   
    @classmethod
    def wt_bt_infos(cls,msg):
        # if len(cls.__btinfos)>120:
        #     cls.__btinfos.pop(0)
        cls.__btinfos.append(msg)

    @classmethod
    def cl_bt_infos(cls):
        cls.__btinfos=[]


    __note='延迟选择_黄金坑_涨停板股票'
    @classmethod
    def have_note(cls):
        return cls.__note
    @classmethod
    def set_note(cls,note=''):
        cls.__note=note
    
    def get_close_price_ma(self, security, n, unit='1d'):

        closeN_data = self.getdatabyname(security)
        ma_n = np.mean([closeN_data[-i] for i in range(n)])
        return ma_n

    def filter_gem_stock(self, stock_list):
        return [stock for stock in stock_list if
                (stock[0:3] != '300') and (stock[0:3] != '900') and (stock[0:3] != '688')]

    def filter_paused_stock(self, stock_list):
        # current_data = get_current_data()
        if self.p.seltype==0:
            nowdate = self.datas[0].datetime.date(0).strftime("%Y%m%d")
            df = pro.suspend_d(**{
                "ts_code": "",
                "trade_date": nowdate,
            }, fields=[
                "ts_code",
                "suspend_type"
            ])
            stoplist_list = df[df['suspend_type'] == 'S']["ts_code"].tolist()
            for stock in stock_list:
                if stock in stoplist_list:
                    stock_list.remove(stock)
                else:
                    continue

            return stock_list
        elif self.p.seltype==1:
            return_list=[]
            alllist=views.havesharealllist()
            for stock in stock_list:
                stock_1=str(stock)[0:6]
                if stock_1 in alllist:
                    return_list.append(stock)
            return return_list

    def filter_limitup_stock(self, stock_list):
        for stock in stock_list:
            # if stock in limit_list:
            # if self.getpositionbyname(stock).size <= 0:
            if self.getdatabyname(stock).limit_status[0] == 1:
                stock_list.remove(stock)
            else:
                continue

        return stock_list
    
    # 2-2 过滤模块-过滤ST及其他具有退市标签的股票
    # 输入选股列表，返回剔除ST及其他具有退市标签股票后的列表
    def filter_st_stock(self, stock_list):
        
        return_list=[]
        alllist=views.havesharealllist()
        for stock in stock_list:
            stock_1=str(stock)[0:6]
            if stock_1 in alllist:
                return_list.append(stock)
        return return_list


     ##过滤上市时间不满指定天数的股票
    def filter_stock_by_days(self, stock_list, days):
        if self.p.seltype==0:
            df = pro.stock_basic(**{
                "ts_code": "",
                "name": "",
            }, fields=[
                "ts_code",
                "symbol",
                "list_date"
            ])
            df["list_date"] = pd.to_datetime(df["list_date"]).dt.date
            nowdate = str(self.datas[0].datetime.date(0).strftime("%Y%m%d"))
            nowdate = pd.to_datetime(nowdate).date()
            df["listdays"] = [(nowdate - df["list_date"])[i].days for i in range(df["list_date"].size)]
            havestocklist = (df["ts_code"][df["listdays"] < days]).tolist()

            for stock in stock_list:
                if stock in havestocklist:
                    stock_list.remove(stock)
                else:
                    continue

            return stock_list
        elif self.p.seltype==1:
            import fu_t1.usemysql as usemysql
            ussql = usemysql.UseMysql()
            return_list=[]
             # 获取基本数据
            for stock in stock_list:
                sharecode=str(stock)[0:6]
                strsql = 'select Symbol,Listdt from companybasicinfo  where (Symbol = \'' + str(
                            sharecode) + '\')'
            
                base_pd = ussql.havedata(strsql)
                if base_pd.size<=0:
                    continue
                base_pd["Listdt"] = pd.to_datetime(base_pd["Listdt"]).dt.date
                nowdate = str(self.datas[0].datetime.date(0).strftime("%Y-%m-%d"))
                nowdate = pd.to_datetime(nowdate).date()
                base_days = (nowdate - base_pd["Listdt"].values[0]).days
                if base_days>days:
                    return_list.append(stock)
            return return_list
                                                
    def print_position_info(self):
        
        for data in self.datas:
            securities = data._name
            position = self.getposition(data=data)
            price = position.price
            amount = position.size
            if amount <= 0:
                continue
            value = price * amount
            
            self.log('持仓代码:{0},现价:{1},持仓(股):{2},市值:{3}'.format(securities,format(price,'.2f'),amount,
                                                          format(value, '.2f')))

    def start(self):
        self.cl_bt_infos()
        # self.wt_bt_infos('开始回测...')
        # print('开始回测...')

    def log(self, txt, dt=None, doprint=True, index=0):
        """ Logging function fot this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[index].datetime.date(0)
            msg='%s  %s' % (dt.isoformat(), txt)
            self.wt_bt_infos(msg)
            print(msg)

    def notify_order(self, order, index=0):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(str(order.params.data._name) +
                         '：买票-价格: %.2f, 成本: %.2f, 费用：%.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(str(order.params.data._name) + '：卖票-价格: %.2f, 成本: %.2f, 费用:%.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('交易取消/拒绝')
        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade, index=0):
        if not trade.isclosed:
            return
        self.log('交易收益-毛利：%.2f, 净利：%.2f' %
                 (trade.pnl, trade.pnlcomm))
     

    def __init__(self):
        # 交易设置的常规属性值
        self.stocknum =self.__selffactors['max_hold_stock_nums'][0]  # 理想持股数量
        self.bearpercent = self.__selffactors['bearpercent'][0]
        self.isbull = False
        self.threshold = self.__selffactors['threshold'][0]  # 牛熊切换阈值
        # 配置择时
        self.MA = [self.p.baseindex, self.__selffactors['period'][0]]  # 均线择时

        self.sel_stocklist = []
        self.order = None
        # 设置期开始的bar
        self.startcount = self.__selffactors['startcount'][0]
        self.countnum = 0
         # 添加技术指标
###########################################################
        teckindexcondict=self.__teckindexcondict
        self.havesharelistbytech(self.getdatanames(),teckindexcondict)
        ########定义保存的选择的股票
        
        self.myfile_forsaveselcodes =pd.DataFrame(columns=['检测时间','策略名称',
                                                            '选股列表','条件因子',
                                                            '动量因子','技术因子',
                                                            '策略条件'])
    def next(self):

        self.countnum = self.countnum + 1
        if self.countnum < self.startcount:
            return
        if self.countnum ==self.startcount+1:
            self.log('#######################开始回测#######################')
        try:
            if self.order:
                print(self.order.status)
                return
        except:
            print('报错')
        self.print_position_info()
        # 每天选择一次股票
        self.before_market_open()
        teckindexcondict=self.__teckindexcondict
        if len(teckindexcondict.keys())>0:
               sel_list=[]
               for conkey in teckindexcondict.keys():
                    if conkey == 'RSI':
                         currlist=[]
                         for code in self.sel_stocklist:
                              if self.Rsindicator_dict[code][0] >0:
                                   currlist.append(code)
                         if len(sel_list)<=0:
                              sel_list=currlist
                         else:
                              sel_list=np.intersect1d(sel_list,currlist)
                         
                    elif conkey == 'MACD':
                         currlist=[]
                         for code in self.sel_stocklist:
                              if self.MACD_dict[code][0] >0:
                                   currlist.append(code)
                         if len(sel_list)<=0:
                              sel_list=currlist
                         else:
                              sel_list=np.intersect1d(sel_list,currlist)
                    elif conkey == 'MEAN':
                         currlist=[]
                         for code in self.sel_stocklist:
                              if self.MEAN_dict[code][0] >0:
                                   currlist.append(code)
                         if len(sel_list)<=0:
                              sel_list=currlist
                         else:
                              sel_list=np.intersect1d(sel_list,currlist)
                    elif conkey == 'KDJ':
                         currlist=[]
                         for code in self.sel_stocklist:
                              if self.KDJ_dict[code][0] >0:
                                   currlist.append(code)
                         if len(sel_list)<=0:
                              sel_list=currlist
                         else:
                              sel_list=np.intersect1d(sel_list,currlist)
                    elif conkey == 'Bias':
                         currlist=[]
                         for code in self.sel_stocklist:
                              if self.Bias_dict [code][0] >0:
                                   currlist.append(code)
                         if len(sel_list)<=0:
                              sel_list=currlist
                         else:
                              sel_list=np.intersect1d(sel_list,currlist)
                    elif conkey == 'BOLL':
                         currlist=[]
                         for code in self.sel_stocklist:
                              if self.BOLL_dict[code][0] >0:
                                   currlist.append(code)
                         if len(sel_list)<=0:
                              sel_list=currlist
                         else:
                              sel_list=np.intersect1d(sel_list,currlist)
               self.sel_stocklist=sel_list
        
        ## 判断是否连续增长
        # highlist= self.high_continous(self.sel_stocklist)
        ## 选择涨停板股票
        limitlist=self.pick_high_limit(self.sel_stocklist)
         ## 选择黄金坑股票
        vallylist=self.check_first_valley(self.sel_stocklist)
        # 设置股票
        self.sel_stocklist=np.union1d(limitlist,vallylist)
        self.log('选择的股票列表:'+str(self.sel_stocklist))
        ###保存选择的股票列表
        if len(self.sel_stocklist)>0:
            cols=self.myfile_forsaveselcodes.columns
            temp_pd=pd.DataFrame(columns=cols)
            temp_pd.loc[0,cols[0]]=self.datas[0].datetime.date(0). strftime('%Y-%m-%d')
            temp_pd.loc[0,cols[1]]=str(self.__note)
            if len(self.sel_stocklist)>1:
                temp_pd.loc[0,cols[2]]=','.join(self.sel_stocklist)+'\t'
            else: 
                temp_pd.loc[0,cols[2]]=self.sel_stocklist[0]+'\t'
            # condition='条件因子:'+str(self.__conditiondict)+'-动量因子:'+str(self.__strongcondition)+'-技术因子:'+str(self.__teckindexcondict)
            temp_pd.loc[0,cols[3]]=''
            temp_pd.loc[0,cols[4]]=''
            temp_pd.loc[0,cols[5]]=''
            temp_pd.loc[0,cols[6]]=''
          
            if self.myfile_forsaveselcodes.size<=0:
                self.myfile_forsaveselcodes =temp_pd
            else:
                self.myfile_forsaveselcodes =pd.concat([self.myfile_forsaveselcodes,temp_pd]) 
        # 根据选择的股票，进行买卖
        self.market_open()

    def stop(self):
        # self.cl_bt_infos()
        self.log('终值: %.2f' %
                 (self.broker.getvalue()), doprint=True)
        totalvalue = self.broker.getvalue()
        sum_weight = 0.0
        for data in self.datas:
            dataSize = self.broker.getposition(data).size
            if dataSize <= 0:
                continue
            dataPrice = self.broker.getposition(data).price
            thisdatavalue = dataSize * dataPrice
            thisvaluesweight = thisdatavalue / totalvalue
            sum_weight += thisvaluesweight
            self.log(str(data._name) + ',价值: %.2f,权重:  %.5f'
                     % (thisdatavalue, thisvaluesweight), doprint=True)
        self.log('本次资产组合的占比之和是%.5f' % sum_weight)
        self.log('回测结束...')
        self.savesel_codes()
        ## 开盘时运行函数

    def market_open(self):
         ##按照市值排序,取最小值
        if len(self.sel_stocklist)>0:
            buyselllist = []
            dtype = [('name', 'S9'), ('marketvalue', np.float)]
            data_mk = [
                (self.sel_stocklist[i], self.getdatabyname(self.sel_stocklist[i]).marketvalue[0])
                for i in range(len(self.sel_stocklist))]
            data_mk = np.array(data_mk, dtype=dtype)
            data_mk = np.sort(data_mk, order='marketvalue')
            for i in range(len(data_mk)):
                buyselllist.append(str(data_mk[i][0], 'UTF-8'))
            self.sel_stocklist = buyselllist
        else:
            return
        ######首先判断哪些股票要卖
        minnum = min(self.stocknum, len(self.sel_stocklist))
        self.sel_stocklist=self.sel_stocklist[0:int(minnum)]
        sell_stock = []
        
        for data in self.datas:
            if self.getposition(data=data).size > 0:
                day_open_price = data.open[0]
                pre_date = data.datetime.date(-1).strftime("%Y-%m-%d")
                pre_close_price = data.close[-1]
                low_allday = data.low[0]
                high_allday = data.high[0]
                current_price = data.close[0]  # 持仓股票的当前价
                cost = self.broker.getposition(data).price
                # close_data = data.close[0]
                # 连续三天的涨幅
                sum_limit_num_three = np.log(data.close[-3] / data.close[0]) > 0.3
                ma5 = np.mean([data.close[i] for i in range(-4,1,-1)])
                max_till = np.max([data.high[i] for i in range(-self.countnum,1,1)])
                if (data._name not in self.sel_stocklist) and (data.limit_status[0]==0):
                    self.log("#1.卖出股票{0},不在股票列表中,同时没有涨停，卖出".format(data._name))
                    sell_stock.append(data._name)
                    self.order_target_value(data, 0)
                elif current_price < cost * 0.95:
                    self.log("#2.卖出股票{0}:亏5个点".format(data._name))
                    sell_stock.append(data._name)
                    # self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                elif current_price < day_open_price * 0.95 and current_price > cost * 1.4:
                    self.log("#3.卖出股票{0}:小于开盘价的0.95,并且超过成本的40%".format(data._name))
                    sell_stock.append(data._name)
                    # self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                # 高位十字星
                elif (current_price < high_allday * 0.97 and day_open_price > low_allday * 1.05) and (
                        day_open_price < high_allday * 0.95 and current_price > cost * 1.4):
                    self.log("#3.卖出股票{0}:收盘价小于最高价的0.97,开盘价大于最低价的1.05,开盘价小于最高价的0.95".format(data._name))
                    sell_stock.append(data._name)
                    # self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                elif sum_limit_num_three and day_open_price < pre_close_price and current_price < pre_close_price * 0.97:
                    self.log("4.卖出股票{0}:三天涨幅超过30%,低开,收盘价小于昨天收盘价0.97".format(data._name))
                    sell_stock.append(data._name)
                    self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                elif current_price < day_open_price * 0.95 and current_price < max_till and current_price > cost * 1.4:
                    self.log("5.卖出股票{0}:收盘价小于开盘价的0.95,收盘价小于60日的最大值".format(data._name))
                    sell_stock.append(data._name)
                    # self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                elif current_price > cost * 1.4 and current_price < ma5:
                    self.log("6.卖出股票{0}:收盘价小于5天的均值".format(data._name))
                    sell_stock.append(data._name)
                    # self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                elif current_price < data.low[-1] * 0.97:
                    self.log("7.卖出股票{0}:小于昨日最低价的3%".format(data._name))
                    sell_stock.append(data._name)
                    # self.sel_stocklist.remove(data._name)
                    self.order_target_value(data, 0)
                # elif day_open_price < low_allday:
                #     self.log("8.卖出股票：开盘价小于最低价")
                #     sell_stock.append(data._name)
                #     self.sel_stocklist.remove(data._name)
                #     self.order_target_value(data, 0)
        ###得到现在还持有多少个股票,并且得到还有多少资金
        holdcount=0
        havecash = self.broker.getcash()
        for data in self.datas:
            if self.getposition(data=data).size > 0:
                holdcount=holdcount+1
                # havecash = havecash - self.getposition(data=data).size * self.getposition(data=data).price
        
        if len(self.sel_stocklist) == 0:
            return
        if holdcount >=(self.stocknum):
            return
        more_holdnum=min(len(self.sel_stocklist),(self.stocknum-holdcount))
        self.sel_stocklist=self.sel_stocklist[0:int(more_holdnum)]
        buycash = havecash / len(self.sel_stocklist)
        self.log('实际股票交易列表' + str(self.sel_stocklist))
        for stock in self.sel_stocklist:
            if self.getpositionbyname(name=stock).size > 0:
                continue
            if stock in sell_stock > 0:
                continue
            nowdata = self.getdatabyname(stock)
            day_open_price = nowdata.open[0]
            current_price = nowdata.close[0]
            pre_close_price = nowdata.close[-1]
            # 连续三天的涨幅
            sum_limit_num_three = (np.log(nowdata.close[-2] /current_price) > 0.03) and (
                    nowdata.close[-2] > nowdata.open[-2]) and (nowdata.close[-1] > nowdata.open[-1])
            #如果股票涨停，不参与买卖
            if nowdata.limit_status[0]==1:
                continue
            if current_price > day_open_price * 1.02 and current_price > pre_close_price and day_open_price < pre_close_price * 1.05 and day_open_price > pre_close_price * 0.99:
                self.log("1." + stock + "买入金额" + str(buycash))
                self.order = self.order_target_value(nowdata, buycash)

            elif day_open_price > pre_close_price * 1.05 and current_price > pre_close_price * 1.03:
                self.log("2." + stock + "买入金额" + str(buycash))
                self.order = self.order_target_value(nowdata, buycash)

            elif nowdata.high[0] > nowdata.low[0] * 1.09:
                # 价格波动大于0.09
                self.log("2." + stock + "买入金额" + str(buycash))
                self.order = self.order_target_value(nowdata, buycash)
            elif sum_limit_num_three:
                # 连涨，今天回调
                self.log("3." + stock + "买入金额" + str(buycash))
                self.order = self.order_target_value(nowdata, buycash)

       

    ## 开盘前运行函数
    def before_market_open(self):
        check_out_list = self.getdatanames()
        check_out_list.remove(self.MA[0])
     
        conditiondict= self.__conditiondict
        strongcondition= self.__strongcondition
        if len(conditiondict.keys())>0:
          check_out_list=self.haveallsharebyconditions_singleday(codelist=check_out_list,conditiondict=conditiondict)
        isstrongok=False
        try:
          for key in strongcondition.keys():
               if len(strongcondition[key].keys())>0:
                    isstrongok=True
        except:
          isstrongok=False
        if isstrongok:
          check_out_list=self.havestrongsharecode(codelist=check_out_list,strongcondition=strongcondition)
        # self.sel_stocklist=check_out_list
        

        # 过滤掉今天涨停的
        check_out_list = self.filter_limitup_stock(check_out_list)
        check_out_list = self.filter_gem_stock(check_out_list)
        check_out_list = self.filter_st_stock(check_out_list)
        # check_out_list = self.filter_paused_stock(check_out_list)
        check_out_list = self.filter_stock_by_days(check_out_list, 100)
        self.sel_stocklist=check_out_list
        
        #判断股票是不是连续增长
        
        
        
       
        # print(self.sel_stocklist)

    # 查询最近最高点的位置，筛选连续增长股票
    def high_continous(self,stocklist):
        return_list=[]
        for stock in stocklist:
            
            data = self.getdatabyname(stock)
            
            data_open = [data.open[i] for i in range(-39,1,1)]
            data_close = [data.close[-i] for i in range(-39,1,1)]
            data_high = [data.high[-i] for i in range(-39,1,1)]

            high_max_index = -np.argmax(data_high)

            df_panel_40_close = data.close.get(ago=high_max_index, size=12)
        
            date_now = self.datas[0].datetime.date(0).strftime("%Y-%m-%d")
            if date_now == '2022-10-13':
                print(df_panel_40_close)
            df_max_close_40 = np.max(df_panel_40_close)
            df_min_close_40 = np.min(df_panel_40_close)
            # 前40日的最大与最小的变化比例

            rate_40 = (df_max_close_40 - df_min_close_40) / df_max_close_40

            
            df_max_high_60 = np.max(data.high.get(ago=high_max_index, size=60))
            # df_max_high_60 = bt.Max([data.high[i] for i in range(-high_max_index, -high_max_index - 60, -1)])

            # df_max_high_60 = np.max([data.high[i] for i in range(-high_max_index, -data.high.buflen(), -1)])
            df_min_low_60 = np.min(data.close.get(ago=high_max_index, size=60))
            # df_min_low_60 = np.min([data.close[-i] for i in range(-high_max_index,-high_max_index-60,step=-1)])
            # df_min_low_60 = np.min(data.close[:-high_max_index])
            # 前60日的每日最大与每日最小的变化比例
            rate_60 = (df_max_high_60 - df_min_low_60) / df_min_low_60

            # print("stock="+stock)
            # print(time_high)

            # pre_date = (time_high + timedelta(days=-1)).strftime("%Y-%m-%d")  # '2021-01-15'#datetime.datetime.now()
            df_panel_eight_close = data.close.get(ago=high_max_index - 1, size=8)
            # [data.close[i] for i in range(-high_max_index - 1, -high_max_index - 8, -1)]
            df_panel_eight_open = data.open.get(ago=high_max_index - 1, size=8)
            # [data.open[i] for i in
            #                    range(-high_max_index - 1, -high_max_index - 8, -1)]
            # 查询涨停板有没有四个
            # 1 检测条件
            sum_limit_num_eight_two = np.sum(data.limit_status.get(ago=high_max_index - 1, size=8))
            # [data.limit_status[i] for i in range(-high_max_index - 1, -high_max_index - 8, -1)])
            # 2 在最高价之前，收盘低于开盘价的次数
            sum_down_eight = np.sum([1 if df_panel_eight_close[i] < df_panel_eight_open[i] else 0 for i in
                                    range(8)])
            # 3 在本次时间的前40天不要有跌破14%的情形

            sum_plus_num_40 = np.sum([1 if (data_open[i] > data_close[i] * 1.14) else 0 for i in range(-40,0,1)])

            # 4 在本次时间的前40天不要有跌破14%的情形
            df_max_high = np.max(data.high.get(ago=high_max_index - 1, size=8))
            # [data.high[i] for i in range(-high_max_index - 1, -high_max_index - 8, -1)].max()

            ## 5当前时间的前六天有多少个涨停板
            sum_limit_num_five = np.sum(data.limit_status.get(ago=-2, size=6))

            # 6查询是不是有10天是低于前一天的

            df_panel_10_close = data.close.get(ago=-2, size=10)
            # [data.close[i] for i in range(-2, -12, -1)]

            df_panel_10_preclose = data.preclose.get(ago=-2, size=10)
            # [data.preclose[i] for i in
            #                     range(start=-2, stop=-12, step=-1)]

            sum_close_low_pre_close = np.sum(
                [1 if df_panel_10_close[i] < df_panel_10_preclose[i] else 0 for i in range(10)])

            # 得到此次数据所有的收盘的最高价
            df_max_high_all = np.max(data.close)

            if sum_limit_num_eight_two >= 3 and \
                    sum_down_eight <= 3 and \
                    sum_plus_num_40 == 0 and \
                    df_max_high > df_max_high_all and \
                    rate_40 >= 0.55 and rate_60 < 3.8 and \
                    sum_close_low_pre_close >= 5 and \
                    sum_limit_num_five == 0:
                
                df_open_one = data.open[-1]
                df_high_one = data.high[-1]

                df_close_two = data.close[-2]
                df_open_two = data.open[-2]

                df_high_two = data.high[-2]
                df_low_two = data.low[-2]
                # 是不是底部十字星
                rate_two = abs(df_close_two - df_open_two) / ((df_close_two + df_open_two) / 2)
                # 十字星最大最小差值小于0.08
                rate_two_high = abs(df_high_two - df_low_two) / ((df_high_two + df_low_two) / 2)

                df_close_three = data.close[-3]
                df_high_limit_three = data.limit_status[-3]
                df_close_mean_60 = self.get_close_price_ma(stock, 60)
                # 底分型
                if df_high_limit_three == 1 \
                        and df_close_two > df_close_mean_60 \
                        and rate_two < 0.025 and \
                        rate_two_high < 0.08 and \
                        df_open_one > df_close_two * 1.02 and \
                        df_open_one > df_open_two * 1.02 and \
                        df_close_three > df_close_two * 1.07 and \
                        df_close_three > df_open_one:
                    return_list.append(stock)
        return return_list
    ##选出打板的股票
    def pick_high_limit(self,stocklist):
        # 'chggrowth':[0.3,'调整幅度'],
         # 'chgturnover':[0.20,'换手幅度'],
        high_limit_stock = []
        for stock in stocklist:
            numoflimits = self.__selffactors['numoflimits'][0]
            if numoflimits>5 or numoflimits<=0:
                numoflimits=2

            chggrowth = self.__selffactors['chggrowth'][0]
            if chggrowth>0.2 or chggrowth<=0:
                chggrowth=0.05

            chgturnover = self.__selffactors['chgturnover'][0]
            if (chgturnover>100) or (chgturnover<=0):
                chgturnover=30

            data = self.getdatabyname(stock)
            # [data.limit_status[i] for i in range(-numoflimits,0,1)]
            sumoflimits=np.sum([data.limit_status[i] for i in range(-int(numoflimits),0,1)])
            istodayok=(np.log(data.close[0])-np.log(data.close[-1]))<chggrowth
            issumsof=(sumoflimits>=numoflimits)
            istodayturnsok=  data.turnover_rate[0]>chgturnover
            isproturnsok=  data.turnover_rate[0]<chgturnover*0.2
            if (stock[0:3] == '300' or stock[0:3] == '688'or stock[0:3] == '301'):
                continue
            if istodayok and issumsof and istodayturnsok and isproturnsok:
                high_limit_stock.append(stock)
        return high_limit_stock

    # 检查是否存在黄金坑
    def check_first_valley(self,stocklist):
        return_list=[]
        for stock in stocklist:
            int_count =int(self.__selffactors['inicount'][0])
            if (int_count>5) or (int_count<1) :
                int_count=1
            # growth=self.__selffactors['growth'][0]
            # if growth>0.3:
            #     growth=0.05
            testperiod=int(self.__selffactors['testperiod'][0])
            if (testperiod>10) or (testperiod<5):
                testperiod=5
            downgrowth=self.__selffactors['downgrowth'][0]
            if (downgrowth>0.5) or (downgrowth<=0):
                downgrowth=0.1
            
            middlegrowth=self.__selffactors['middlegrowth'][0]
            if middlegrowth>0.5:
                middlegrowth=0.02
            upgrowth=self.__selffactors['upgrowth'][0]
            if upgrowth>0.3 or upgrowth<=0:
                upgrowth=0.05

            todaygrowth=self.__selffactors['todaygrowth'][0]
            if todaygrowth>0.3 or todaygrowth<=0:
                todaygrowth=0.05  

            meangrowth=self.__selffactors['meangrowth'][0]
            if meangrowth>0.25 or meangrowth<0:
                meangrowth=0.05  

            data = self.getdatabyname(stock)
            # for i in range(-1, -31, -1):
                
            pre_close_price = data.close[-int_count]
            
            df_panel_p = data.close.get(ago=-int_count, size=testperiod)
            firstperiod=int(np.ceil(testperiod*0.3))
            middleperiod=int(np.ceil(testperiod*0.6))
            isfirstok =(np.log(df_panel_p[0])-np.log(df_panel_p[firstperiod]))> downgrowth
            if middleperiod==firstperiod:
                ismiddleok=(np.log(data.close[-(testperiod-middleperiod-1)])-np.log(data.close[-(testperiod-middleperiod-1)-1]))<middlegrowth
            else:
                ismiddleok=np.std(df_panel_p[firstperiod:middleperiod])<middlegrowth
            isupok=(np.log(df_panel_p[testperiod-1])-np.log(df_panel_p[middleperiod]))> upgrowth
            istodayup= (np.log(data.close[0])-np.log(pre_close_price))>todaygrowth
            
            df_close_mean_5 = np.mean(df_panel_p)
            ismenaok=(np.log(pre_close_price )-np.log(df_close_mean_5))>meangrowth
            if ismenaok and isfirstok and ismiddleok and isupok and istodayup:
                return_list.append(stock)
                
            #     break
            # if int_count > 5:
            #     break
                # int_count = int_count +1
        return  return_list

   

    ## 收盘后运行函数
    def after_market_close(self):
        date_now = self.datas[0].datetime.date(0).strftime("%Y-%m-%d")
        print(str('函数运行时间(after_market_close):' + str(date_now)))
        # 得到当天所有成交记录
        for stock_remove in self.sel_stocklist:
            self.sel_stocklist.remove(stock_remove)
        
        print('##############################################################')