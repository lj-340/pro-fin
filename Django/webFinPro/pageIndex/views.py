
from ast import Raise
from cmath import nan
from collections import UserString
import http
import os
from urllib.parse import uses_params

from django.http import HttpResponse, Http404, FileResponse,JsonResponse
import datetime as dt
from django.shortcuts import render
from pageIndex.models import *
from  pageIndex.forms import *
#import akshare as ak
import pandas as pd
from fu_t1 import BackTrade_IndustryRoll
from fu_t1 import BackTrade_ShareByCondition
from fu_t1 import BackTrade_ShareChoiceByFactors
from django.contrib.auth import authenticate
from django.conf import settings
import tushare as ts
# Load tushare token from environment variable to avoid hardcoding secrets.
tushare_token = os.environ.get('TUSHARE_TOKEN')
if tushare_token:
     ts.set_token(tushare_token)
     pro = ts.pro_api()
else:
     pro = None
# 保存服务器状态
serverparams={
'connectparams':{
          'connectnums':0,
          'connectUsers':[],
          'connecthostnames':[]
          },
'computerparams':{
                '估值模型':0,
                '相关性模型':0,
                '因子模型':0,
                '多维模型':0,
                '预测模型':0,
                '行业轮转':0,
                },
'computerinfo':'服务器正常',

}
# 保存用户执行的数据
userparams=[]
##数据库选择标志
sel_havedatasourcetype=1 # 0代表从tushare中获取，1代表从自身数据中获取
def updateServerstate(modulname,username,method):
     moduleslist=serverparams['computerparams'].keys()
     moduleslist=list(moduleslist)
     if method=='add':
          if modulname in moduleslist:
                serverparams['computerparams'][modulname] =serverparams['computerparams'][modulname]+1
                serverparams['connectparams']['connectnums']=serverparams['connectparams']['connectnums']+1
                if not (username in serverparams['connectparams']['connectUsers']):
                         serverparams['connectparams']['connectUsers'].append(str(username))
          else:
                serverparams['computerparams'][modulname] =1
                serverparams['connectparams']['connectnums']=serverparams['connectparams']['connectnums']+1
                if not (username in serverparams['connectparams']['connectUsers']):
                         serverparams['connectparams']['connectUsers'].append(str(username))
     elif method=='delete':
           if modulname in moduleslist:
                serverparams['computerparams'][modulname] =serverparams['computerparams'][modulname]-1
                if serverparams['computerparams'][modulname]<0:
                    serverparams['computerparams'][modulname]=0
                serverparams['connectparams']['connectnums']=serverparams['connectparams']['connectnums']-1
                if serverparams['connectparams']['connectnums']<0:
                    serverparams['connectparams']['connectnums']=0
                if  (username in serverparams['connectparams']['connectUsers']):
                    serverparams['connectparams']['connectUsers'].remove(username)
     
     
     
     if len(userparams)>0:
          
          if method=='add':
               if not(username in  userparams):
                    userparams.append(username ) 
          elif method=='delete':
                 if username in  userparams:
                    userparams.remove(username)        
     else:
          if method=='add':
               userparams.append(username) 


# 初始化服务器状态
def initialServerstate(session):  
     serverparams={
     'connectparams':{
               'connectnums':0,
               'connectUsers':[],
               'connecthostnames':[]
               },
     'computerparams':{
                    '估值模型':0,
                    '相关性模型':0,
                    '因子模型':0,
                    '多维模型':0,
                    '预测模型':0,
                    '行业轮转':0,
                    },
     'computerinfo':'All For Profit !',
     } 
     views.serverparams=serverparams
     views.userparams=dict()
     

# 保存一个管理员用户列表
adminuserslist=['bochuan','fin-tech']
# 保存提高级用户列表
upuserslist=['up_fin_len','honghong']
# 保存普通级用户列表
genuserslist=['gen_fin_or']

def convertnulltozero(strnumber):
     try:
          returnfloat =float(strnumber)
          return returnfloat
     except:
          if strnumber=='':
               return 0
          else:
               raise RuntimeError('无法转变')


def haveservestate(request):
     if request.method=='GET':
          username=request.session.get('username','')
          if username =='':
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})
          else:
               if username in adminuserslist:
                    return JsonResponse(serverparams)
               else:
                  serverstate={'computerparams':{
                                        '估值模型':0,
                                        '相关性模型':0,
                                        '因子模型':0,
                                        '多维模型':0,
                                        '预测模型':0,
                                        '行业轮转':0,
                                             },
                                        'computerinfo':'',}
                  serverstate['connectparams']=''
                  serverstate['computerparams']=serverparams['computerparams']
                  serverstate['computerinfo']=serverparams['computerinfo']
                  serverstate=np.array(serverstate).tolist()
                  return JsonResponse(serverstate)
     else:
          return HttpResponse('norequest')
def haveparams(request):
     if request.method=='GET':
          username=request.session.get('username','')
          if username =='':
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})
          else:
               if(request.is_ajax):
                    dataprocesstype=  request.GET['dataprocesstype']
                    
                    resultjson={'serverstate':'','errormessage':''
                    }
                    if serverparams['connectparams']['connectnums'] <6:
                         if len(userparams)>0:
                              if username in userparams:
                                   resultjson['serverstate']='ERROR'
                                   return JsonResponse(resultjson)
                              else:
                                   resultjson['serverstate']='OK'
                                   return JsonResponse(resultjson)
                         else:
                              resultjson['serverstate']='OK'
                              return JsonResponse(resultjson)
                    else:
                         resultjson['serverstate']='ERROR'
                         return JsonResponse(resultjson)
               else:
                    logins=LoginForm(request.POST)
                    return render(request, "pageIndex/logins.html",{'form':logins})
     else:
          return HttpResponse('norequest')
def servestate(request):
     username=request.session.get('username','')
     if not(username ==''):
          #return render(request, "pageIndex/servestate.html")      
          return render(request, "pageIndex/servestate.html")  
     else:
          logins=LoginForm(request.POST)
          return render(request, "pageIndex/logins.html",{'form':logins})
 #else:
     # return HttpResponse('norequest')
# 增加条件
def accessvalue(request):
     if request.method == "POST":
          username=request.session.get('username','')
          if username =='':
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})
          else:
               if (request.is_ajax):
                    try:
                         myform = accessvalueForm(request.POST,(username))
                    
                         tradeconditionsdict,financeconditionsdict=haveconditionlist()
                         resultjson={'accessresults':0,'resultparams':dict(),'errormessage':''}
                         if myform.is_valid():
                              from fu_t1 import BackTrade_AssessValue
                              form= request.POST
                              updateServerstate('估值模型',username,'add')
                              #serverparams['computerparams']['估值模型']=1
                              startdate= str(form.getlist('startdate')[0]).strip() # dcf中作为验证股票代码时间
                              enddate=str(form.getlist('enddate')[0]).strip() # dcf中作为截止时间
                              if enddate < startdate:
                                   raise RuntimeError('结束时间不能小于开始时间!')
          
                              accesstypevalue=str(form.getlist('accesstype')[0])
                              # 获得数据源类型
                              datasourcetype=form.getlist('sources')[0]
                              # 获得数据源中选择了哪些板块
                              selectedconceptnames=form.getlist('datasourenamelist')
                              ###############
                              sharecode=str(form.getlist('sharecode')[0]).strip()
                              from  fu_t1.BackTrade_Factors import FactorsTest
                              factTest = FactorsTest(start_date=startdate, end_date=enddate)
                              isgoodshare=factTest.cleansingleshare(sharecode=sharecode,startdate=startdate, enddate=enddate)
                              if not isgoodshare:
                                   raise RuntimeError('输入的股票代码有误!请重新输入')
                              accesstypeinfo='本次估值选择:'
                              if accesstypevalue=='isliquids':
                                   accesstypeinfo=accesstypeinfo+"现金流折现:"
                                   sharePriceValue = BackTrade_AssessValue.AssessValue()
                                   dcytype=int(convertnulltozero(form.getlist('dcftype')[0]))
                                   dcftype_second_num=int(convertnulltozero(form.getlist('dcftype_second')[0]))
                                   dcftype_third_num=int(convertnulltozero(form.getlist('dcftype_third')[0]))
                                   dcfliquid=convertnulltozero(form.getlist('dcfliquid')[0])
                                   dcfwacc=convertnulltozero(form.getlist('sharewacc')[0])
                                   dcfRs=convertnulltozero(form.getlist('shareRs')[0])
                                   dcfRb=convertnulltozero(form.getlist('shareRb')[0])
                                   dcfhigh=convertnulltozero(form.getlist('highgrowth')[0])
                                   dcfsteady=convertnulltozero(form.getlist('steadygrowth')[0])
                                   dcfparas = {'dcfliquid': dcfliquid,
                                                  'dcfwacc': [dcfwacc,dcfRs,dcfRb], # 所有国企的资本成本是0.055
                                                                      # 第一个值是wacc，第二个Rs股权成本，第三个是Rb债务成本
                                                  'dcfgrowth': [dcfhigh, dcfsteady]}  # 第一个值是高速增长，第二个是长期稳定增长
                                                                      
                                   #isbeltaUseOls=form.getlist('havebelta_ols')[0]
                                   isbeltaUseOls=False
                                   if len(form.getlist('havebelta_ols'))>0:
                                        isbeltaUseOls=True
                                   sharelist=[]
                                   # 默认不回归belta
                                   isbeltaUseOls=False
                                   if isbeltaUseOls:
                                        sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=selectedconceptnames)
                                        if len(sharelist)==0:
                                             raise RuntimeError('选择了belta_ols,需要选择股票!')
                                   dcfparas, shareprice,procesmessage= sharePriceValue.value_by_liquid(sharecode=sharecode,
                                                                 startdate=enddate,
                                                                 dcfparas=dcfparas,
                                                                 lastPeriods=dcftype_second_num,  # 二阶段模型中高速增长年限
                                                                 twoPeriods=dcftype_third_num,  # 三阶段模型中第二个高速增长年限
                                                                 modeltype=dcytype,  # 现金流估值的不同模型
                                                                 numsofyear=4,  # 可持续增长率取几年的增长率，# 三阶段是他的2倍
                                                                 beltaUseOls=isbeltaUseOls,  # 是否采用ols计算belta值
                                                                 sharelist=sharelist,  # 如果采用ols计算belta，则需要提供股票列表
                                                                 stablegrowthvar='F082601B', # 稳定增长采用developdata中的可持续增长率
                                                                 fastgrowthvar='ROIC2' # 高速增长采用 evaseasondata 中的ROIC
                                                                 )
                                   resultjson={'accessresults':0,'resultparams':dict(),'errormessage':''}
                                   resultjson['accessresults']='股票价格('+str(sharecode)+')='+str(shareprice)
                                   # json不支持array数据类型
                                   if dcytype==2:
                                        resultjson['resultparams']= str({'现金流':str(dcfparas['dcfliquid']),
                                                                      '折现成本(wacc)':dcfparas['dcfwacc'][0],
                                                                      '股权成本(Rs)':dcfparas['dcfwacc'][1],
                                                                      '债权成本(Rb)':dcfparas['dcfwacc'][2],
                                                                      '快速增长(Gg)':dcfparas['dcfgrowth'][0],
                                                                      '稳定增长(Gs)':dcfparas['dcfgrowth'][1],
                                                                      })
                                   elif dcytype==1:
                                        resultjson['resultparams']= str({'现金流':str(dcfparas['dcfliquid']),
                                                                      '折现成本(wacc)':dcfparas['dcfwacc'][0],
                                                                      '股权成本(Rs)':dcfparas['dcfwacc'][1],
                                                                      '债权成本(Rb)':dcfparas['dcfwacc'][2],
                                                                      '稳定增长(Gg)':dcfparas['dcfgrowth'],
                                                                      })
                                   elif dcytype==3:
                                        pass
                                   
                                   #resultjson['resultparams']=str(dcfparas)
                                   # procesmessage=accesstypeinfo+';'+procesmessage
                                   resultjson['processinfo']=procesmessage
                                   updateServerstate('估值模型',username,'delete')
                                   #serverparams['computerparams']['估值模型']=0
                                   return JsonResponse(resultjson)

                              elif accesstypevalue=='isfactors':# 多因子估值
                                   accesstypeinfo=accesstypeinfo+"多因子估值:"
          
                                   # sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=selectedconceptnames)
                                   # if len(sharelist)==0:
                                   #      raise RuntimeError('没有选择板块')
                                   if len(selectedconceptnames)<=0:
                                        havesel_filename='人工概念分类'
                                        filepath=settings.BASE_DIR+"/static/download/"+username+'/'
                                        filelist =os.listdir(filepath)
                                        valuefilelist = []
                                        for file in filelist:
                                             if str(file).find(havesel_filename)>=0:
                                                  valuefile = os.path.join(filepath, file)
                                                  if os.path.isfile(valuefile):
                                                       if valuefile.endswith('.csv'):
                                                            valuefilelist.append(valuefile)
                                        # forwarfilename=filepath
                                        if len(valuefilelist)>0:
                                             valuefilelist.sort()
                                             selectfile=valuefilelist[-1]
                                             # forwarfilename=os.path.splitext(selectfile)[0]
                                             # 代表检测的代码
                                             datasourcetype='em_concept'
                                             selectedconceptnames=pd.read_csv(selectfile,encoding='GBK')['板块名称'].tolist()
                                        else:
                                             raise RuntimeError('需要至少需要选择1个板块或者设置人工模块') 
                                       
                                   if len(selectedconceptnames)==1:
                                        sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=selectedconceptnames)
                                        isdeletelowcorrlist=False
                                        if len(form.getlist('isdeletelowcorrlist'))>0:
                                             isdeletelowcorrlist=True
                                        if isdeletelowcorrlist:
                                             corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                             if (corr_sd) <= 0 or(corr_sd >=1):
                                                  raise RuntimeError('筛选标准要0~1')
                                             method='corr'
                                             result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                                 start_date=startdate,
                                                                 end_date=enddate,
                                                                 groupcode=sharelist,
                                                                 method=method, grouptype = 'isinnergroup')
                                             result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                             concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                             for countindex in range(len(concept_cons_em_df)):
                                                  concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                             
                                             sharelist=concept_cons_em_df

                                        findfactors=form.getlist('finfactors')
                                        numData=int(form.getlist('num_of_data_year')[0])*2
                                        responsetype=form.getlist('responsetype')[0]
                                        if responsetype=='isreturn':
                                             responsetype='pcg'
                                        elif responsetype=='ispe':
                                             responsetype='pe'
                                        elif responsetype=='isps':
                                             responsetype='ps'
                                        elif responsetype=='ispb':
                                             responsetype='pb'  
                                        elif responsetype=='isev_ebitda':
                                             responsetype='ev_ebitda'  
                                        oslstring=''
                                        if len(findfactors) >0:
                                             for keyvalue in findfactors:
                                                  if (keyvalue=='total_asset') or (keyvalue=='total_debt'):
                                                       keyvalue='np.log('+keyvalue+')'
                                                  if oslstring=='':
                                                       oslstring=keyvalue
                                                  else:
                                                       oslstring=oslstring+'+'+keyvalue
                                        else:
                                             raise RuntimeError('没有选择指标!')
                                        result_pd, datasize= factTest.factorsEffectiveT1_Multishare_finance(sharelist=sharelist,
                                                                                          method='ols',
                                                                                          Yvar=responsetype,
                                                                                          tradedate=enddate,
                                                                                          numofreturn=numData,
                                                                                          olsstring=oslstring,
                                                                                          conditions=findfactors)
                                        if result_pd.shape[0]<=0:
                                             raise RuntimeError('没有获取回归数据')
                                        shareprice=''
                                        
                                        sharecode_pd=factTest.updateSingleFinanceConditions(sharecode=str(sharecode),tradedate=enddate,
                                                                                     conditions=findfactors)
                                        # for col in sharecode_pd.columns:
                                        #      if np.array(sharecode_pd.loc[:,col]).all()==np.nan:
                                        #           raise RuntimeError(str(sharecode)+':列='+col+'没有数据')
                                        sharecode_pd=sharecode_pd.fillna(0)
                                   
                                        keyinfo=''
                                        shareprice=result_pd[result_pd['变量名'] =='constant'].loc[0,'斜率']
                                        for key in findfactors:
                                             try:
                                                  keymean= sharecode_pd[key].mean()
                                                  if keymean==0:
                                                       keyinfo=keyinfo+''+str(key)+'没有数据！ '

                                                  print(key)
                                                  if (key=='total_asset') or (key=='total_debt'):
                                                       key_log='np.log('+key+')'
                                                       shareprice=shareprice+result_pd[result_pd['变量名'] ==key_log].loc[0,'斜率'] * np.log(keymean)
                                                  else:
                                                       shareprice = shareprice + result_pd[result_pd['变量名'] == key].loc[0, '斜率'] * (keymean)
                                             except Exception as e:
                                                  print(key+':报错!')
                                                  continue
                                        shareprice=round(shareprice,5)

                                        resultjson={'accessresults':0,'resultparams':dict(),'processinfo':'','errormessage':''}
                                        resultjson['accessresults']='股票('+str(sharecode)+')'+keyinfo+' '+responsetype+'='+str(shareprice)
                                        result_pd_col=result_pd.columns
                                        result_pd_array= np.insert( np.array(result_pd), 0, values=result_pd_col, axis=0)
                                        result_pd_list=result_pd_array.tolist()
                                        resultjson['resultparams']=result_pd_list
                                        resultjson['processinfo']=accesstypeinfo+'选择板块空间:'+str(selectedconceptnames)+'共有:'+str(len(sharelist))+'个股票;响应变量='+str(responsetype)+';共有:'+str(datasize)+'个数据'
                                        updateServerstate('估值模型',username,'delete')
                                        #serverparams['computerparams']['估值模型']=0
                                        return JsonResponse(resultjson)
                                   elif len(selectedconceptnames)>1:
                                        allresult_pd=pd.DataFrame()
                                        
                                        for conceptname in selectedconceptnames:
                                             try:
                                                  sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=[conceptname])
                                                  
                                                  isdeletelowcorrlist=False
                                                  if len(form.getlist('isdeletelowcorrlist'))>0:
                                                       isdeletelowcorrlist=True
                                                  if isdeletelowcorrlist:
                                                       corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                                       if (corr_sd) <= 0 or(corr_sd >=1):
                                                            raise RuntimeError('筛选标准要0~1')
                                                       method='corr'
                                                       result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                                           start_date=startdate,
                                                                           end_date=enddate,
                                                                           groupcode=sharelist,
                                                                           method=method, grouptype = 'isinnergroup')
                                                       result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                                       concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                                       for countindex in range(len(concept_cons_em_df)):
                                                            concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                                       
                                                       sharelist=concept_cons_em_df

                                                  findfactors=form.getlist('finfactors')
                                                  numData=int(form.getlist('num_of_data_year')[0])
                                                  responsetype=form.getlist('responsetype')[0]
                                                  if responsetype=='isreturn':
                                                       responsetype='pcg'
                                                  elif responsetype=='ispe':
                                                       responsetype='pe'
                                                  elif responsetype=='isps':
                                                       responsetype='ps'
                                                  elif responsetype=='ispb':
                                                       responsetype='pb'  
                                                  elif responsetype=='isev_ebitda':
                                                       responsetype='ev_ebitda'  
                                                  oslstring=''
                                                  if len(findfactors) >0:
                                                       for keyvalue in findfactors:
                                                            if (keyvalue=='total_asset') or (keyvalue=='total_debt'):
                                                                 keyvalue='np.log('+keyvalue+')'
                                                            if oslstring=='':
                                                                 oslstring=keyvalue
                                                            else:
                                                                 oslstring=oslstring+'+'+keyvalue
                                                  else:
                                                       raise RuntimeError('没有选择指标!')
                                                  result_pd, datasize= factTest.factorsEffectiveT1_Multishare_finance(sharelist=sharelist,
                                                                                                    method='ols',
                                                                                                    Yvar=responsetype,
                                                                                                    tradedate=enddate,
                                                                                                    numofreturn=numData,
                                                                                                    olsstring=oslstring,
                                                                                                    conditions=findfactors)
                                                  if result_pd.shape[0]<=0:
                                                       continue
                                                  shareprice=''
                                                  
                                                  sharecode_pd=factTest.updateSingleFinanceConditions(sharecode=str(sharecode),tradedate=enddate,
                                                                                               conditions=findfactors)
                                                  # for col in sharecode_pd.columns:
                                                  #      if np.array(sharecode_pd.loc[:,col]).all()==np.nan:
                                                  #           raise RuntimeError(str(sharecode)+':列='+col+'没有数据')
                                                  sharecode_pd=sharecode_pd.fillna(0)
                                             
                                                  keyinfo=''
                                                  shareprice=result_pd[result_pd['变量名'] =='constant'].loc[0,'斜率']
                                                  for key in findfactors:
                                                       try:
                                                            keymean= sharecode_pd[key].mean()
                                                            if keymean==0:
                                                                 keyinfo=keyinfo+''+str(key)+'没有数据！ '

                                                            print(key)
                                                            if (key=='total_asset') or (key=='total_debt'):
                                                                 key_log='np.log('+key+')'
                                                                 shareprice=shareprice+result_pd[result_pd['变量名'] ==key_log].loc[0,'斜率'] * np.log(keymean)
                                                            else:
                                                                 shareprice = shareprice + result_pd[result_pd['变量名'] == key].loc[0, '斜率'] * (keymean)
                                                       except Exception as e:
                                                            print(key+':报错!')
                                                            continue
                                                  shareprice=round(shareprice,5)
                                                  temp_result_pd=pd.DataFrame()
                                                  temp_result_pd.loc[0,'股票代码']=sharecode+'\t'
                                                  temp_result_pd.loc[0,'截止时间']=str(enddate)
                                                  temp_result_pd.loc[0,'响应变量']=str(responsetype)
                                                  temp_result_pd.loc[0,'估值结果']=str(np.around(shareprice,3))
                                                  temp_result_pd.loc[0,'板块名称']=conceptname
                                                  temp_result_pd.loc[0,'拟合优度']=str(np.around(result_pd['R值'].tolist()[0],3))
                                                  temp_result_pd.loc[0,'股票个数']=str(len(sharelist))
                                                  temp_result_pd.loc[0,'数据数量']=str(datasize)
                                                  ##现在的相应变量是多少
                                                  if sel_havedatasourcetype==1:
                                                       strsql = ''
                                                       import fu_t1.usemysql as usemysql
                                                       ussql = usemysql.UseMysql()

                                                       if responsetype=='pe':
                                                            strsql = 'select Symbol,TradingDate,PE1TTM from valuedata where((Symbol = \'' + str(
                                                                 sharecode) + '\') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前市盈率(pe_ttm)']=str(have_res['PE1TTM'].tolist()[0])
                                                       if responsetype=='ps':
                                                            strsql = 'select Symbol,TradingDate,PSTTM from valuedata where((Symbol = ' + str(
                                                                 sharecode ) + ') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前市销率(ps_ttm)']=str(have_res['PSTTM'].tolist()[0])
                                                       if responsetype=='pb':
                                                            strsql = 'select Symbol,TradingDate,PBV1B from valuedata where((Symbol = ' + str(
                                                                 sharecode ) + ') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前市净率(pb)']=str(have_res['PBV1B'].tolist()[0])
                                                       if responsetype=='ev_ebitda':
                                                            strsql = 'select Symbol,TradingDate,EV2ToEBITDA from valuedata where((Symbol = ' + str(
                                                                 sharecode ) + ') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前价值倍数']=str(have_res['EV2ToEBITDA'].tolist()[0]) 
                                                       temp_result_pd=temp_result_pd.fillna(0)    
                                                       if allresult_pd.size<=0:
                                                            allresult_pd=temp_result_pd
                                                       else:
                                                            allresult_pd=pd.concat([allresult_pd,temp_result_pd])
                                                  elif sel_havedatasourcetype==0:
                                                       if str.startswith(sharecode, '6'):
                                                            sharecode_tu = sharecode + '.SH'
                                                       else:
                                                            sharecode_tu  = sharecode + '.SZ'
                                                       have_res = pro.daily_basic(**{
                                                                      "ts_code": sharecode_tu,
                                                                      "limit": 1,
                                                                      }, fields=[
                                                                           "ts_code",
                                                                           "trade_date",
                                                                           "pe_ttm",
                                                                           "pb",
                                                                           "ps_ttm",
                                                                           ])
                                                       if responsetype=='pe':
                                                       
                                                            temp_result_pd.loc[0,'当前市盈率(pe_ttm)']=str(np.around(have_res['pe_ttm'].tolist()[0],3))
                                                       if responsetype=='ps':
                                                       
                                                            temp_result_pd.loc[0,'当前市销率(ps_ttm)']=str(np.around(have_res['ps_ttm'].tolist()[0],3))
                                                       if responsetype=='pb':
                                                            
                                                            temp_result_pd.loc[0,'当前市净率(pb)']=str(np.around(have_res['pb'].tolist()[0],3))
                                                       if responsetype=='ev_ebitda':
                                                       
                                                            temp_result_pd.loc[0,'当前价值倍数']=str(0) 
                                                       temp_result_pd=temp_result_pd.fillna(0)     
                                                       if allresult_pd.size<=0:
                                                            allresult_pd=temp_result_pd
                                                       else:
                                                            allresult_pd=pd.concat([allresult_pd,temp_result_pd])
                                             except Exception as e:
                                                  print(conceptname)
                                                  print(e)
                                                  continue
                                        if allresult_pd.size>0:
                                             ##########生成文件并保存
                                             industfilename='多因子估值-多板块'
                                             savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                                             industfilename=industfilename+'('+startdate+'-'+enddate+')'
                                             nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                                             industfilename=industfilename+'-'+username+'('+nowtime+')' +'.csv'
                                             
                                             filepath = os.path.join(savelocation,industfilename)
                              
                                             allresult_pd.to_csv(filepath, index=False, encoding='GBK')
                                             #文件生成后，再发送邮件
                                             sendbacktraderesult(filepath,username,'多因子估值-多板块('+sharecode+')','多因子估值','估值结果.csv') 
                                             ###########       
                                             resultjson={'accessresults':0,'resultparams':dict(),'processinfo':'','errormessage':''}
                                             resultjson['accessresults']='股票('+str(sharecode)+')'+keyinfo+' '+responsetype+'='+str(shareprice)
                                             result_pd_col=allresult_pd.columns
                                             result_pd_array= np.insert( np.array(allresult_pd), 0, values=result_pd_col, axis=0)
                                             result_pd_list=result_pd_array.tolist()
                                             resultjson['resultparams']=result_pd_list
                                             resultjson['processinfo']=accesstypeinfo+'选择板块空间:'+str(selectedconceptnames)
                                             updateServerstate('估值模型',username,'delete')
                                             #serverparams['computerparams']['估值模型']=0
                                             return JsonResponse(resultjson)  
                                        else:
                                             raise RuntimeError('没有回去估值数据')  
                              elif accesstypevalue=='isrelatives':
                                   accesstypeinfo=accesstypeinfo+'相对价值回归:'
                                   sharePriceValue = BackTrade_AssessValue.AssessValue()
                                   if len(selectedconceptnames)<=0:
                                        havesel_filename='人工概念分类'
                                        filepath=settings.BASE_DIR+"/static/download/"+username+'/'
                                        filelist =os.listdir(filepath)
                                        valuefilelist = []
                                        for file in filelist:
                                             if str(file).find(havesel_filename)>=0:
                                                  valuefile = os.path.join(filepath, file)
                                                  if os.path.isfile(valuefile):
                                                       if valuefile.endswith('.csv'):
                                                            valuefilelist.append(valuefile)
                                        # forwarfilename=filepath
                                        if len(valuefilelist)>0:
                                             valuefilelist.sort()
                                             selectfile=valuefilelist[-1]
                                             # forwarfilename=os.path.splitext(selectfile)[0]
                                             # 代表检测的代码
                                             datasourcetype='em_concept'
                                             selectedconceptnames=pd.read_csv(selectfile,encoding='GBK')['板块名称'].tolist()
                                        else:
                                             raise RuntimeError('需要至少需要选择1个板块或者设置人工模块') 
                                   if len(selectedconceptnames)==1:
                                        sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=selectedconceptnames)
                                        if len(sharelist)==0:
                                             raise RuntimeError("相对价值估算,需要选择股票!")
                                        isdeletelowcorrlist=False
                                        if len(form.getlist('isdeletelowcorrlist'))>0:
                                             isdeletelowcorrlist=True
                                        if isdeletelowcorrlist:
                                             corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                             factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                             if (corr_sd) <= 0 or(corr_sd >=1):
                                                  raise RuntimeError('筛选标准要0~1')
                                             method='corr'
                                             result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                                 start_date=startdate,
                                                                 end_date=enddate,
                                                                 groupcode=sharelist,
                                                                 method=method, grouptype = 'isinnergroup')
                                             result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                             concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                             for countindex in range(len(concept_cons_em_df)):
                                                  concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                             
                                             sharelist=concept_cons_em_df
                                        #isbeltaUseOls=form.getlist('havebelta_ols')[0]
                                        isbeltaUseOls=False
                                        if len(form.getlist('havebelta_ols_relative'))>0:
                                             isbeltaUseOls=True
                                        if isbeltaUseOls:
                                             if len(sharelist)==0:
                                                  raise RuntimeError('选择了belta_ols,需要选择股票')
                                        # 默认不回归belta
                                        isbeltaUseOls=False
                                        responsetype=form.getlist('relativevaluetype')[0]
                                        if responsetype=='ispe':
                                             responsetype='pe'
                                        elif responsetype=='isps':
                                             responsetype='ps'
                                        elif responsetype=='ispb':
                                             responsetype='pb'  
                                        elif responsetype=='isev_ebitda':
                                             responsetype='ev_ebitda' 
                                        Xparams = {}
                                        resultsPd_by_ols = pd.DataFrame()
                                        resultsPd_by_ols, Xparams, sharePrice,regnum,processinfo = \
                                             sharePriceValue.value_by_relative(
                                                  startdate=enddate,
                                                  enddate='',
                                                  noriskrate=0,
                                                  sharecode=sharecode,
                                                  sharelist=sharelist,
                                                  modeltype=responsetype,  # 支持pe pb ps ev_ebitda
                                                  numofyears=1,  # 取多长时间的数据进行回归，默认是1年，默许是不采用
                                                  Xparams=dict(),
                                                  beltaUseOls=False,# belta值得获取方式
                                                  beltavar='Beta1', # 这是对应数据库中中列名 singleriskdata
                                                  growthvar='F080801B', # 这是对应数据库中中列名 developdata
                                                  divvar='F110301B',  # 这是对应数据库中中列名sharedividenddata
                                                  roevar='F050504C', # profitdata
                                                  netprofitvar='F053301C' ,# profitdata数据库
                                                  debtvar='F011201A', #   debtdata 数据库
                                             )
                                        
                                        resultjson={'accessresults':0,'resultparams':dict(),'processinfo':'','errormessage':''}
                                        resultjson['accessresults']='股票('+str(sharecode)+')'+responsetype+'='+str(sharePrice)
                                        # 获取回归参数
                                        resultsPd_by_ols_col=resultsPd_by_ols.columns
                                        resultsPd_by_ols_array= np.insert( np.array(resultsPd_by_ols), 0, values=resultsPd_by_ols_col, axis=0)
                                        result_pd_list=resultsPd_by_ols_array.tolist()
                                        resultjson['resultparams']= result_pd_list
                                        # 回归过程参数
                                        processinfo=accesstypeinfo+',选择板块空间:'+str(selectedconceptnames)+',共有:'+str(len(sharelist))+'个股票,共有'+str(regnum)+'个数据;选择'+ str(responsetype)+';股票自身参数=' + str(Xparams)+';'+processinfo
                                        resultjson['processinfo']=processinfo
                                        updateServerstate('估值模型',username,'delete')
                                        #serverparams['computerparams']['估值模型']=0
                                        return JsonResponse(resultjson)
                                   elif len(selectedconceptnames)>1:
                                        allresult_pd=pd.DataFrame()
                                        for conceptname in  selectedconceptnames:
                                             try:
                                                  sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=[conceptname])
                                                  if len(sharelist)==0:
                                                       raise RuntimeError("相对价值估算,需要选择股票!")
                                                  isdeletelowcorrlist=False
                                                  if len(form.getlist('isdeletelowcorrlist'))>0:
                                                       isdeletelowcorrlist=True
                                                  if isdeletelowcorrlist:
                                                       corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                                       factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                                       if (corr_sd) <= 0 or(corr_sd >=1):
                                                            raise RuntimeError('筛选标准要0~1')
                                                       method='corr'
                                                       result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                                           start_date=startdate,
                                                                           end_date=enddate,
                                                                           groupcode=sharelist,
                                                                           method=method, grouptype = 'isinnergroup')
                                                       result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                                       concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                                       for countindex in range(len(concept_cons_em_df)):
                                                            concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                                       
                                                       sharelist=concept_cons_em_df
                                                  #isbeltaUseOls=form.getlist('havebelta_ols')[0]
                                                  isbeltaUseOls=False
                                                  if len(form.getlist('havebelta_ols_relative'))>0:
                                                       isbeltaUseOls=True
                                                  if isbeltaUseOls:
                                                       if len(sharelist)==0:
                                                            raise RuntimeError('选择了belta_ols,需要选择股票')
                                                  # 默认不回归belta
                                                  isbeltaUseOls=False
                                                  responsetype=form.getlist('relativevaluetype')[0]
                                                  if responsetype=='ispe':
                                                       responsetype='pe'
                                                  elif responsetype=='isps':
                                                       responsetype='ps'
                                                  elif responsetype=='ispb':
                                                       responsetype='pb'  
                                                  elif responsetype=='isev_ebitda':
                                                       responsetype='ev_ebitda' 
                                                  Xparams = {}
                                                  resultsPd_by_ols = pd.DataFrame()
                                                  resultsPd_by_ols, Xparams, sharePrice,regnum,processinfo = \
                                                       sharePriceValue.value_by_relative(
                                                            startdate=enddate,
                                                            enddate='',
                                                            noriskrate=0,
                                                            sharecode=sharecode,
                                                            sharelist=sharelist,
                                                            modeltype=responsetype,  # 支持pe pb ps ev_ebitda
                                                            numofyears=2,  # 取多长时间的数据进行回归，默认是1年，默许是不采用
                                                            Xparams=dict(),
                                                            beltaUseOls=False,# belta值得获取方式
                                                            beltavar='Beta1', # 这是对应数据库中中列名 singleriskdata
                                                            growthvar='F080801B', # 这是对应数据库中中列名 developdata
                                                            divvar='F110301B',  # 这是对应数据库中中列名sharedividenddata
                                                            roevar='F050504C', # profitdata
                                                            netprofitvar='F053301C' ,# profitdata数据库
                                                            debtvar='F011201A', #   debtdata 数据库
                                                       )
                                                  temp_result_pd=pd.DataFrame()
                                                  temp_result_pd.loc[0,'股票代码']=sharecode+'\t'
                                                  temp_result_pd.loc[0,'截止时间']=str(enddate)
                                                  temp_result_pd.loc[0,'响应变量']=str(responsetype)
                                                  temp_result_pd.loc[0,'估值结果']=str(np.around(sharePrice,3))
                                                  temp_result_pd.loc[0,'板块名称']=conceptname
                                                  temp_result_pd.loc[0,'拟合优度']=str(np.around(resultsPd_by_ols['R值'].tolist()[0],3))
                                                  temp_result_pd.loc[0,'股票个数']=str(len(sharelist))
                                                  temp_result_pd.loc[0,'数据数量']=str(regnum)
                                                  ##现在的相应变量是多少
                                                  if sel_havedatasourcetype==1:
                                                       strsql = ''
                                                       import fu_t1.usemysql as usemysql
                                                       ussql = usemysql.UseMysql()

                                                       if responsetype=='pe':
                                                            strsql = 'select Symbol,TradingDate,PE1TTM from valuedata where((Symbol = \'' + str(
                                                                 sharecode) + '\') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前市盈率(pe_ttm)']=str(have_res['PE1TTM'].tolist()[0])
                                                       if responsetype=='ps':
                                                            strsql = 'select Symbol,TradingDate,PSTTM from valuedata where((Symbol = ' + str(
                                                                 sharecode ) + ') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前市销率(ps_ttm)']=str(have_res['PSTTM'].tolist()[0])
                                                       if responsetype=='pb':
                                                            strsql = 'select Symbol,TradingDate,PBV1B from valuedata where((Symbol = ' + str(
                                                                 sharecode ) + ') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前市净率(pb)']=str(have_res['PBV1B'].tolist()[0])
                                                       if responsetype=='ev_ebitda':
                                                            strsql = 'select Symbol,TradingDate,EV2ToEBITDA from valuedata where((Symbol = ' + str(
                                                                 sharecode ) + ') and  (TradingDate   <= \'' + str(enddate) + '\')) ' + ' Order by TradingDate DESC limit 1 '
                                                            have_res=ussql.havedata(strsql)
                                                            temp_result_pd.loc[0,'当前价值倍数']=str(have_res['EV2ToEBITDA'].tolist()[0]) 
                                                       temp_result_pd=temp_result_pd.fillna(0)    
                                                       if allresult_pd.size<=0:
                                                            allresult_pd=temp_result_pd
                                                       else:
                                                            allresult_pd=pd.concat([allresult_pd,temp_result_pd])
                                                  elif sel_havedatasourcetype==0:
                                                       if str.startswith(sharecode, '6'):
                                                            sharecode_tu = sharecode + '.SH'
                                                       else:
                                                            sharecode_tu  = sharecode + '.SZ'
                                                       have_res = pro.daily_basic(**{
                                                                      "ts_code": sharecode_tu,
                                                                      "limit": 1,
                                                                      }, fields=[
                                                                           "ts_code",
                                                                           "trade_date",
                                                                           "pe_ttm",
                                                                           "pb",
                                                                           "ps_ttm",
                                                                           ])
                                                       if responsetype=='pe':
                                                       
                                                            temp_result_pd.loc[0,'当前市盈率(pe_ttm)']=str(np.around(have_res['pe_ttm'].tolist()[0],3))
                                                       if responsetype=='ps':
                                                       
                                                            temp_result_pd.loc[0,'当前市销率(ps_ttm)']=str(np.around(have_res['ps_ttm'].tolist()[0],3))
                                                       if responsetype=='pb':
                                                            
                                                            temp_result_pd.loc[0,'当前市净率(pb)']=str(np.around(have_res['pb'].tolist()[0],3))
                                                       if responsetype=='ev_ebitda':
                                                       
                                                            temp_result_pd.loc[0,'当前价值倍数']=str(0) 
                                                       temp_result_pd=temp_result_pd.fillna(0)     
                                                       if allresult_pd.size<=0:
                                                            allresult_pd=temp_result_pd
                                                       else:
                                                            allresult_pd=pd.concat([allresult_pd,temp_result_pd])
                                             except Exception as e:
                                                  print(conceptname)
                                                  print(e)
                                                  continue
                                        if allresult_pd.size>0:
                                             ##########生成文件并保存
                                             industfilename='相对价值估值-多板块'
                                             savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                                             industfilename=industfilename+'('+startdate+'-'+enddate+')'
                                             nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                                             industfilename=industfilename+'-'+username+'('+nowtime+')' +'.csv'
                                             
                                             filepath = os.path.join(savelocation,industfilename)
                              
                                             allresult_pd.to_csv(filepath, index=False, encoding='GBK')
                                             #文件生成后，再发送邮件
                                             sendbacktraderesult(filepath,username,'相对价值估值-多板块('+sharecode+')','相对价值估值','估值结果.csv')          
                                             resultjson={'accessresults':0,'resultparams':dict(),'processinfo':'','errormessage':''}
                                             resultjson['accessresults']='股票('+str(sharecode)+')'+'响应变量='+responsetype
                                             # 获取回归参数
                                             resultsPd_by_ols_col=allresult_pd.columns
                                             resultsPd_by_ols_array= np.insert( np.array(allresult_pd), 0, values=resultsPd_by_ols_col, axis=0)
                                             result_pd_list=resultsPd_by_ols_array.tolist()
                                             resultjson['resultparams']= result_pd_list
                                             # 回归过程参数
                                             processinfo=accesstypeinfo+',选择板块空间:'+str(selectedconceptnames)
                                             resultjson['processinfo']=processinfo
                                             updateServerstate('估值模型',username,'delete')
                                             #serverparams['computerparams']['估值模型']=0
                                             return JsonResponse(resultjson)
                                        else:
                                             raise RuntimeError('没有回去相对价值估值数据')

                         else:
                              raise RuntimeError()
                    except Exception as e:
                         updateServerstate('估值模型',username,'delete')
                         #serverparams['computerparams']['估值模型']=0
                         resultjson['errormessage']=str(e)
                         resultjson['accessresults']='ERROR'
                         return JsonResponse(resultjson)
               else:
                    try:
                         myform = accessvalueForm(request.POST,(username))
                    
                         tradeconditionsdict,financeconditionsdict=haveconditionlist()
                         filename=''
                         updateServerstate('估值模型',username,'delete')
                         #serverparams['computerparams']['估值模型']=0
                         return render(request, "pageIndex/accessvalue.html",{'form':myform,
                                                                           'filename':filename,
                                                                           'username':username,
                                                                           'tradeconditionsdict':tradeconditionsdict,
                                                                           'financeconditionsdict':financeconditionsdict}) 
                    except Exception as e:
                         print(e)
                         
                         filename=''
                         updateServerstate('估值模型',username,'delete')
                         #serverparams['computerparams']['估值模型']=0
                         return render(request, "pageIndex/accessvalue.html",{'form':myform,
                                                                           'filename':filename,
                                                                           'errormessage':str(e),
                                                                           'username':username,
                                                                           'tradeconditionsdict':tradeconditionsdict,
                                                                           'financeconditionsdict':financeconditionsdict}) 
          
     else:
          username=request.session.get('username','')
          if not(username ==''):
               if  not (request.is_ajax):
                    myform = accessvalueForm(request.POST,(username))
                    
                    tradeconditionsdict,financeconditionsdict=haveconditionlist()
                    filename=''
                    return render(request, "pageIndex/accessvalue.html",{'form':myform,
                                                                      'filename':filename,
                                                                      'username':username,
                                                                      'tradeconditionsdict':tradeconditionsdict,
                                                                      'financeconditionsdict':financeconditionsdict}) 
               else:
                    try:
                         resultjson={'error_message':'',
                         
                         'datasoure':dict(),
                         }
                         datasourcevalue=str(request.GET['datasourcevalue'])
                         alllistname=havealllistname(datasourcevalue)
                         if len(alllistname)<=0:
                              raise RuntimeError('没有找到数据')
                         
                         resultjson['datasoure']=np.array(alllistname).tolist()
                         
                         return JsonResponse(resultjson)
                    except Exception as e:
                         resultjson={'error_message':'',
                         'datasoure':'',
                         }
                         resultjson['error_message']=str(e)
                         print(e)
                         return JsonResponse(resultjson)

               
          else:
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})

def haveusername(request):
     return request.session.get('username','')

def correlations(request):
     if request.method == "POST":
        username=request.session.get('username','')
        if username =='':
          logins=LoginForm(request)
          return render(request, "pageIndex/logins.html",{'form':logins})
        else:    
          try:
              
               myform =correlationsForm(request.POST,(username))
               if myform.is_valid(): #提供验证判断是否有效，成立则返回是Ture
                         # 表示开始计算
                         updateServerstate('相关性模型',username,'add')
                         
                         form= request.POST
                         startdate= form.getlist('startdate')[0]
                         enddate=form.getlist('enddate')[0]
                         if enddate < startdate:
                              raise RuntimeError('结束时间不能小于开始时间!')
                         datasourcetype=str(form.getlist('sources')[0])
                        
                         isgroupchecktype=form.getlist('groupchecktype')[0]
                         checktype=form.getlist('checktype')[0]
                         # 得到处理的函数
                         industfilename='相关性模型'
                         for keys in industryprocss.industryprocess.allindustrys_dict.keys():
                              keyname=industryprocss.industryprocess.allindustrys_dict[keys]
                              if datasourcetype==str(keys):
                                   industfilename=industfilename+'-'+str(keyname)
                                   break
                         if isgroupchecktype=='isinnergroup':
                              industfilename=industfilename+'-板块内部'
                         elif isgroupchecktype=='isshareVSshare': 
                              industfilename=industfilename+'-个股VS个股'
                         elif isgroupchecktype=='isshareVSallgroup': 
                              industfilename=industfilename+'-个股VS板块'
                         elif isgroupchecktype=='isgroupVSallshare': 
                              industfilename=industfilename+'-板块VS个股'
                         elif isgroupchecktype=='isgroupVSallgroup': 
                              industfilename=industfilename+'-板块VS板块'
                         if checktype=='isols':
                              isols=True
                              iscorr=False
                              isanova=False
                              industfilename=industfilename+'-多因子(每日收益)'
                         elif checktype=='iscorr':
                              isols=False
                              iscorr=True
                              isanova=False
                              industfilename=industfilename+'-相关性'
                         elif checktype=='isanova':
                              isols=False
                              iscorr=False
                              isanova=True
                              industfilename=industfilename+'-单方差'
                         savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                        
                         industfilename=industfilename+'('+startdate+'-'+enddate+')'
                         nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                         industfilename=industfilename+'-'+username+'('+nowtime+')'
                         if  isols:
                              from  fu_t1.BackTrade_Factors import FactorsTest
                              
                             
                              sharelist=[]
                              sharelistname=[]
                              sharelistname=form.getlist('datasourenamelist')
                              if len(sharelistname)!=1:
                                   raise RuntimeError('需要选择1个板块') 
                              sharelist=havesharelist_fromname(datasourcetype,sharelistname,1)
                              factorstype=''
                              factorkeys=[]
                              selectfactortype=str(form.getlist('factorstype')[0])
                              if selectfactortype=='tradefactors':

                                   factorstype='tradefactors'
                                   
                                   factorkeys=form.getlist('multitradefactorsdatalist')
                              else:
                                   factorstype='financefactors'
                                   
                                   factorkeys=form.getlist('multifinancefactorsdatalist')
                              trade_result=pd.DataFrame()
                              if len(factorkeys)<=0:
                                   raise RuntimeError('至少需要选择1个因子')
                              factTest = FactorsTest(start_date=startdate, end_date=enddate)
                              regmethod='ols'
                              if factorstype=='tradefactors':
                                   for sharecode in sharelist:

                                        try:
                                             pd_dict_trade = factTest.factorsEffectiveT1_singleshare_trade(sharecode=str(sharecode),
                                                                                                         start_date=startdate,
                                                                                                         end_date=enddate,
                                                                                                        regmethod=regmethod,
                                                                                                        conditionskeys=factorkeys)
                                             temp_trade = pd_dict_trade['trade']
                                             if not (temp_trade is None):
                                                  # 保存实时交易回归结果
                                                  if trade_result.size == 0:
                                                       trade_result = temp_trade
                                                  else:
                                                       trade_result = pd.concat([trade_result,temp_trade])
                                             else:
                                                  print(sharecode + ': trade-数据回归错误')
                                   
                                        except Exception as e:
                                             print(str(e)+':'+sharecode)
                                             continue
                              elif factorstype=='financefactors':
                                   for sharecode in sharelist:
                                        sharecode=str(sharecode)
                                        try:
                                             pd_dict_trade = factTest.factorsEffectiveT1_singleshare_finance(sharecode=sharecode,
                                                                                                    regmethod=regmethod,
                                                                                                    start_date=startdate,
                                                                                                    end_date=enddate,
                                                                                                    conditionskeys=factorkeys,
                                                                                                    numofreturn=4)
                                             temp_trade = pd_dict_trade['finance']
                                             if not (temp_trade is None):
                                                  # 保存实时交易回归结果
                                                  if trade_result.size == 0:
                                                       trade_result = temp_trade
                                                  else:
                                                       trade_result = pd.concat([trade_result,temp_trade])
                                             else:
                                                  print(sharecode + ': trade-数据回归错误')
                                   
                                        except Exception as e:
                                             print(str(e)+':'+sharecode)
                                             continue
                              industfilename=industfilename+'-'+str(sharelistname[0])+'.csv'
                              filepath = os.path.join(savelocation,industfilename)
                              if trade_result.size<=0:
                                   raise RuntimeError('没有查到数据')
                              trade_result['股票代码']=trade_result['股票代码']+'\t'
                              trade_result.to_csv(filepath, index=False, encoding='GBK')
                                
                              # 表示已经计算结束
                              updateServerstate('相关性模型',username,'delete')
                              filename=industfilename
                              correlationdict=request.session.get('correlationdict','')
                              if correlationdict=='':
                                   correlationdict=dict()
                                   correlationdict['相关性-线性']=industfilename
                                   request.session['correlationdict']=correlationdict
                              else:
                                   correlationdict['相关性-线性']=industfilename
                                   request.session['correlationdict']=correlationdict
                              ###########发送邮件 
                              sendbacktraderesult(filepath,username,'相关性-线性检测('+str(datasourcetype)+'|'+str(sharelistname)+')','相关性测试','检测结果.csv') 
                              return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                           'username':username,
                                                                           'filename':filename
                                                                           })                             
                         elif iscorr:
                              # 板块内部相关性检测
                              from  fu_t1.BackTrade_Factors import FactorsTest
                              
                              if isgroupchecktype=='isinnergroup':
                                   method='corr'
                                   sharelist=[]
                                   sharelistname=[]
                                   sharelistname=form.getlist('datasourenamelist')
                                   if len(sharelistname)!=1:
                                        raise RuntimeError('需要选择1个板块') 
                                   sharelist= havesharelist_fromname(datasourcetype,sharelistname,1)
                                   # totallist=np.int16(len(sharelist)/4)
                                   # print(totallist)
                                   # sharelist= sharelist[0:totallist]
                                   
                                        
                                   factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                   result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                                      start_date=startdate,
                                                                      end_date=enddate,
                                                                      groupcode=sharelist,
                                                                      method=method, grouptype=isgroupchecktype)
                                  
                                   result_pd=result_pd.sort_values(by='相关系数',ascending=False)
                                   if result_pd.size > 0:
                                        industfilename=industfilename+'-'+str(sharelistname[0])+'.csv'
                                        filepath = os.path.join(savelocation,industfilename)
                                        result_pd.to_csv(filepath, index=False, encoding='GBK')
                                        # 表示已经计算结束
                                        updateServerstate('相关性模型',username,'delete')
                                        filename=industfilename
                                        correlationdict=request.session.get('correlationdict','')
                                        if correlationdict=='':
                                             correlationdict=dict()
                                             correlationdict['相关性-板块内部']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        else:
                                             correlationdict['相关性-板块内部']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        ###########发送邮件 
                                        sendbacktraderesult(filepath,username,'相关性-板块内部('+str(datasourcetype)+'|'+str(sharelistname)+')','相关性测试','检测结果.csv') 
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                     'username':username,
                                                                                  'filename':filename}) 
                                                                                     
                                   else:
                                        errormessage='没有查到数据。。'
                                        # 表示已经计算结束
                                        updateServerstate('相关性模型',username,'delete')
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                           'filename':'',
                                                                           'errormessage':errormessage}) 
               
                              elif isgroupchecktype=='isshareVSallgroup' :
                                   #开始个股对整个板块的相关性检测
                                   factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                   # 首先开始相关性检测：
                                   sharecode=form.getlist('sharecode')[0]
                                   allsharelist=views.havesharealllist()
                                   # sharecode=str(sharecodelist[0])
                                   if not (sharecode in allsharelist):
                                        raise RuntimeError('输入的股票代码有误，重新输入！')
                                   # isgoodshare=factTest.cleansingleshare(sharecode=sharecode,startdate=startdate, enddate=enddate)
                                   # if not isgoodshare:
                                   #      raise RuntimeError('输入的股票代码有误!请重新输入')
                                   rest_pd=pd.DataFrame()
                                   method='corr'
                                   # 得到选择的板块名称
                                   selectsharelistname=form.getlist('datasourenamelist')
                                   if len(selectsharelistname)>50:
                                        raise RuntimeError('板块个数不能超过50') 
                                   if len(selectsharelistname)<=0:
                                        ###可以查找人工有没有设置文件
                                        havesel_filename='人工概念分类'
               
                                        filepath=settings.BASE_DIR+"/static/download/"+username+'/'
                                        filelist =os.listdir(filepath)
                                        valuefilelist = []
                                        for file in filelist:
                                             if str(file).find(havesel_filename)>=0:
                                                  valuefile = os.path.join(filepath, file)
                                                  if os.path.isfile(valuefile):
                                                       if valuefile.endswith('.csv'):
                                                            valuefilelist.append(valuefile)
                                        # forwarfilename=filepath
                                        if len(valuefilelist)>0:
                                             valuefilelist.sort()
                                             selectfile=valuefilelist[-1]
                                             # forwarfilename=os.path.splitext(selectfile)[0]
                                             # 代表检测的代码
                                             datasourcetype='em_concept'
                                             selectsharelistname=pd.read_csv(selectfile,encoding='GBK')['板块名称'].tolist()
                                        else:
                                             raise RuntimeError('需要至少需要选择1个板块或者设置人工模块') 
                                   rest_pd = factTest.shareCorrlattionT1(sharecode=sharecode, 
                                                                                     start_date=startdate,
                                                                                     end_date=enddate,
                                                                                     isEMS_con=False, 
                                                                                     isTHS_indus=False,
                                                                                     isEMS_indus=True,
                                                                                     isTHS_con=False,
                                                                                     grouptype=isgroupchecktype,
                                                                                     datasourcetype=datasourcetype,
                                                                                     selectlist=selectsharelistname,
                                                                                     method=method)
     
                                   if rest_pd.size >0: 
                                        industfilename=industfilename+'-'+str(sharecode)+'-板块'+'.csv'
                                        filepath = os.path.join(savelocation,industfilename)
                                        rest_pd.to_csv(filepath, index=False, encoding='GBK')
                                        # 表示已经计算结束
                                        updateServerstate('相关性模型',username,'delete')
                                        filename=industfilename
                                        correlationdict=request.session.get('correlationdict','')
                                        # 在session中保存文件名
                                        if correlationdict=='':
                                             correlationdict=dict()
                                             correlationdict['相关性-个股VS板块']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        else:
                                             correlationdict['相关性-个股VS板块']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        ###########发送邮件 
                                        sendbacktraderesult(filepath,username,'相关性-个股VS板块('+sharecode+'|'+str(selectsharelistname)+')','相关性测试','检测结果.csv') 
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                     'username':username,
                                                                                  'filename':filename})
                                                                                     
                                   else:
                                        errormessage='没有数据,请重新查询!'
                                        updateServerstate('相关性模型',username,'delete')
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                'filename':'',
                                                                                'errormessage':errormessage}) 
                                                                                       
                              # 个股与选定板块内股票的相关性检测
                              elif isgroupchecktype=='isshareVSshare':
                                   #个股对选定所有板块股票的相关性检
                                   method='corr'
                                   sharecode=form.getlist('sharecode')[0]
                                   from  fu_t1.BackTrade_Factors import FactorsTest
                                   factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                   
                                   # isgoodshare=factTest.cleansingleshare(sharecode=sharecode,startdate=startdate, enddate=enddate)
                                   # if not isgoodshare:
                                   #      raise RuntimeError('输入的股票代码有误!请重新输入')
                                   allsharelist=views.havesharealllist()
                                   # sharecode=str(sharecodelist[0])
                                   if not (sharecode in allsharelist):
                                        raise RuntimeError('输入的股票代码有误，重新输入！')
                                   
                                   sharelist=[]
                                   sharelistname=[]
                                   sharelistname=form.getlist('datasourenamelist')
                                   if len(sharelistname)>=20:
                                        raise RuntimeError('板块个数不能超过20') 
                                   if len(sharelistname)<=0:
                                        raise RuntimeError('需要至少需要选择1个板块') 
                                   sharelist= havesharelist_fromname(datasourcetype,sharelistname,1)
                    
                                   rest_pd = factTest.shareCorrlattionT1(sharecode=sharecode, start_date=startdate,
                                                                      end_date=enddate, grouptype=isgroupchecktype,
                                                                      groupcode=sharelist,
                                                                      method=method)
                                   if rest_pd.size >0:
                                        if len(sharelistname)==1:
                                            industfilename=industfilename+'-'+str(sharecode)+'-('+str(sharelistname[0])+')'+'.csv'  
                                        else:
                                             strconcept='('
                                             for indexstr in range(len(sharelistname)):
                                                  strconcept=strconcept+'-'+sharelistname[indexstr]
                                             strconcept=strconcept+')'

                                             industfilename=industfilename+'-'+str(sharecode)+'-'+strconcept+'.csv'
                                        filepath = os.path.join(savelocation,industfilename)
                                        rest_pd.to_csv(filepath, index=False, encoding='GBK')
                                        # 表示已经计算结束
                                        updateServerstate('相关性模型',username,'delete')
                                        filename=industfilename
                                        # 在session中保存相关数据
                                        correlationdict=request.session.get('correlationdict','')
                                        if correlationdict=='':
                                             correlationdict=dict()
                                             correlationdict['相关性-个股VS个股']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        else:
                                             correlationdict['相关性-个股VS个股']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        ###########发送邮件 
                                        sendbacktraderesult(filepath,username,'相关性-个股VS个股('+sharecode+'|'+str(datasourcetype)+'|'+str(sharelistname)+')','相关性测试','检测结果.csv')
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                     'username':username,
                                                                                  'filename':filename})
                                   else:
                                        errormessage='没有数据,请重新查询!'
                                        updateServerstate('相关性模型',username,'delete')
                                        return render(request, "pageIndex/industryroll.html",{'form':myform,
                                                                                'filename':'',
                                                                                'errormessage':errormessage})
                              elif isgroupchecktype=='isgroupVSallshare':
                                   method='corr'
                                   sharelist=[]
                                   sharelistname=[]
                                   sharelistname=form.getlist('datasourenamelist')
                                   if len(sharelistname)!=1:
                                        raise RuntimeError('需要选择1个板块') 
                                   # 获取所有的股票
                                   sharecodetype=form.getlist('sharecodetype')[0]
                                   sharealllist= havesharealllist()
                                   selectalllist=haveselectalllist(sharealllist,sharecodetype)

                                   # 当前选的股票列表
                                   selectsharelist=havesharelist_fromname(datasourcetype,sharelistname,1)         
                                   factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                    # 是否需要进行筛选，这会影响速度
                                   isdeletelowcorrlist=False
                                   if len(form.getlist('isdeletelowcorrlist'))>0:
                                        isdeletelowcorrlist=True
                                   isdeletelowcorrlist=False
                                   if isdeletelowcorrlist:
                                        corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                        if (corr_sd) <  0 or (corr_sd >=1):
                                             raise RuntimeError('筛选标准要0~1')
                                        if (corr_sd) > 0:
                                             method='corr'
                                             result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=selectsharelist,
                                                                 start_date=startdate,
                                                                 end_date=enddate,
                                                                 groupcode=selectsharelist,
                                                                 method=method, grouptype = 'isinnergroup')
                                             result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                             concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                             for countindex in range(len(concept_cons_em_df)):
                                                  concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                             
                                             selectsharelist=concept_cons_em_df
                                   sharecodetype=form.getlist('sharecodetype')[0]
                                   result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=selectalllist,
                                                                      start_date=startdate,
                                                                      end_date=enddate,
                                                                      groupcode=selectsharelist,
                                                                      method=method, grouptype=isgroupchecktype)

                                   if result_pd.size > 0:
                                        industfilename=industfilename+'-'+str(sharelistname[0])+'.csv'
                                        filepath = os.path.join(savelocation,industfilename)
                                        result_pd.loc[:,'板块名称']=str(sharelistname[0])
                                        result_pd.to_csv(filepath, index=False, encoding='GBK')
                                        # 表示已经计算结束
                                        updateServerstate('相关性模型',username,'delete')
                                        filename=industfilename
                                        correlationdict=request.session.get('correlationdict','')
                                        if correlationdict=='':
                                             correlationdict=dict()
                                             correlationdict['相关性-板块VS个股']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        else:
                                             correlationdict['相关性-板块VS个股']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        # filename=username+'/'+filename
                                        ###########发送邮件 
                                        sendbacktraderesult(filepath,username,'相关性-板块VS个股('+str(sharelistname)+')','相关性测试','检测结果.csv')
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                     'username':username,
                                                                                     'filename':filename}) 
                                                                                     
                                   else:
                                        raise RuntimeError()    
                              elif isgroupchecktype=='isgroupVSallgroup':
                                   method='corr'
                                   sharelist=[]
                                   sharelistname=[]
                                   sharelistname=form.getlist('datasourenamelist')
                                   if len(sharelistname)!=1:
                                        raise RuntimeError('需要选择1个板块') 
                                   
                                   # 选定的股票代码
                                   selectsharelist=havesharelist_fromname(datasourcetype,sharelistname,1)  
                                   
                                   factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                   # 是否需要进行筛选，这会影响速度
                             
                                   isdeletelowcorrlist=False
                                   if len(form.getlist('isdeletelowcorrlist'))>0:
                                        isdeletelowcorrlist=True
                                   # isdeletelowcorrlist=False
                                   if isdeletelowcorrlist:
                                        corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                        if (corr_sd) <= 0 or(corr_sd >=1):
                                             raise RuntimeError('筛选标准要0~1')
                                        method='corr'
                                        result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=selectsharelist,
                                                            start_date=startdate,
                                                            end_date=enddate,
                                                            groupcode=selectsharelist,
                                                            method=method, grouptype = 'isinnergroup')
                                        result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                        concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                        for countindex in range(len(concept_cons_em_df)):
                                             concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                        
                                        selectsharelist=concept_cons_em_df
                                  
                                   rest_pd=pd.DataFrame()
               
                                   rest_pd = factTest.shareCorrlattionT1(start_date=startdate,
                                                                           end_date=enddate,
                                                                           isEMS_con=False, 
                                                                           isTHS_indus=False,
                                                                           isEMS_indus=True,
                                                                           isTHS_con=False,
                                                                           groupcode=selectsharelist,
                                                                           grouptype=isgroupchecktype,
                                                                           datasourcetype=datasourcetype,
                                                                           method=method)
                                                                               
     
                                   if rest_pd.size >0: 
                                        industfilename=industfilename+'-'+str(sharelistname[0])+'.csv'
                                        filepath = os.path.join(savelocation,industfilename)
                                        rest_pd.loc[:,'选择板块']=str(sharelistname[0])
                                        rest_pd.to_csv(filepath, index=False, encoding='GBK')
                                        # 表示已经计算结束
                                        updateServerstate('相关性模型',username,'delete')
                                        filename=industfilename
                                        correlationdict=request.session.get('correlationdict','')
                                        # 在session中保存文件名
                                        if correlationdict=='':
                                             correlationdict=dict()
                                             correlationdict['相关性-板块VS板块']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        else:
                                             correlationdict['相关性-板块VS板块']=industfilename
                                             request.session['correlationdict']=correlationdict
                                        ###########发送邮件 
                                        sendbacktraderesult(filepath,username,'相关性-板块VS板块('+str(sharelistname)+')','相关性测试','检测结果.csv')
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                     'username':username,
                                                                                     'filename':filename})
                                                                                     
                                   else:
                                        errormessage='没有数据,请重新查询!'
                                        updateServerstate('相关性模型',username,'delete')
                                        return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                'filename':'',
                                                                                'errormessage':errormessage})                                   
                         elif isanova:
                              sharelist=[]
                              sharelistname=[]
                              sharelistname=form.getlist('datasourenamelist')
                              if len(sharelistname)!=1:
                                   raise RuntimeError('需要选择1个板块') 
                              sharelist=havesharelist_fromname(datasourcetype,sharelistname,1)
                              method='corr'
                              # 是否需要进行筛选，这会影响速度
                             
                              isdeletelowcorrlist=False
                              if len(form.getlist('isdeletelowcorrlist'))>0:
                                   isdeletelowcorrlist=True
                              isdeletelowcorrlist=False
                              if isdeletelowcorrlist:
                                   factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                   corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                   if (corr_sd) <= 0 or(corr_sd >=1):
                                        raise RuntimeError('筛选标准要0~1')
                                   method='corr'
                                   result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                            start_date=startdate,
                                                            end_date=enddate,
                                                            groupcode=sharelist,
                                                            method=method, grouptype = 'isinnergroup')
                                   result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                   concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                   for countindex in range(len(concept_cons_em_df)):
                                       concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                   
                                   sharelist=concept_cons_em_df
                              factTest = FactorsTest(start_date=startdate, end_date=enddate)
                              anova_temp = factTest.TestFactors_in_group_by_anova(multifactors=sharelist)
                              if anova_temp.size>0:
                                   anova_temp['概念名称'] = str(sharelistname[0])
                                   industfilename=industfilename+'-'+str(sharelistname[0])+'.csv'
                                   filepath = os.path.join(savelocation,industfilename)
                                   anova_temp.to_csv(filepath, index=False, encoding='GBK')                             
                                   # 表示已经计算结束
                                   updateServerstate('相关性模型',username,'delete')
                                   filename=industfilename
                                   # session中保存数据
                                   correlationdict=request.session.get('correlationdict','')
                                   if correlationdict=='':
                                        correlationdict=dict()
                                        correlationdict['相关性_单方差']=industfilename
                                        request.session['correlationdict']=correlationdict
                                   else:
                                        correlationdict['相关性_单方差']=industfilename
                                        request.session['correlationdict']=correlationdict
                                   ###########发送邮件 
                                   sendbacktraderesult(filepath,username,'相关性_单方差','相关性测试','检测结果.csv')
                                   return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                                'username':username,
                                                                                  'filename':filename
                                                                                })
                              else:
                                   errormessage='没有数据,请重新查询!'
                                   serverparams['computerparams']['相关性模型']=0
                                   return render(request, "pageIndex/industryroll.html",{'form':myform,
                                                                           'filename':'',
                                                                           'errormessage':errormessage})
               else:
                    raise RuntimeError('时间格式不对,如:2011-01-02')
          except Exception as e:
               errormessage=str(e)
               print(e)
               # 表示已经计算结束,确保还可以继续计算
               updateServerstate('相关性模型',username,'delete')
               return render(request, "pageIndex/correlations.html",{'form':myform,
                                                  'username':username,
                                                  'filename':'',
                                                  'errormessage':errormessage,
                                                 }) 

     else:
          username=request.session.get('username','')
          if not(username ==''):
               if  not (request.is_ajax):
                    myform = correlationsForm(request.POST,(username))
                    
                    filename=''
                    return render(request, "pageIndex/correlations.html",{'form':myform,
                                                                        'username':username,
                                                                       'filename':''
                                                                        })  
               else:
                    try:
                         resultjson={'error_message':'',
                         'multitradefactorsdata':'',
                         'multifinancefactorsdata':'',
                         'datasoure':dict(),
                         }
                         datasourcevalue=str(request.GET['datasourcevalue'])
                         alllistname=havealllistname(datasourcevalue)
                         multifactorsdata=havetradeconditions()
                         multifinancefactorsdata=havefinanceconditions()
                         resultjson['multitradefactorsdata']=np.array(multifactorsdata).tolist()
                         resultjson['multifinancefactorsdata']=np.array(multifinancefactorsdata).tolist()
                         if len(alllistname)<=0:
                              raise RuntimeError('没有找到数据')
                         
                         resultjson['datasoure']=np.array(alllistname).tolist()
                         
                         return JsonResponse(resultjson)
                    except Exception as e:
                         resultjson={'error_message':'',
                         'multifactorsdata':'',
                         'multifinancefactorsdata':'',
                         'datasoure':'',
                         }
                         resultjson['error_message']=str(e)
                         print(e)
                         return JsonResponse(resultjson)


          else:
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})
 
def industryroll(request):
     if request.method == "POST": #request是 HttpRequest的对象，利用它的的method属性，判断请求方法。
        username=request.session.get('username','')
        if username =='':
          logins=LoginForm(request.POST)
          return render(request, "logins.html",{'form':logins})
        else:
          if request.is_ajax:
               # 开始新建或者删除行业
               try:
                    resultjson={'error_message':'',
                               'serverstate':'',
                               'userindustryinfo':'',
                              }
                    if len(userparams)>0:
                         if username in userparams:
                              resultjson['serverstate']='ERROR'
                              return JsonResponse(resultjson)
                              
                    
                    updateServerstate('行业更新',username,'add')
                    industryprocess=industryprocss.industryprocess('更新行业')
                    resultjson=industryprocess.update_user_industry(myform=request.POST,username=username)
                    
                    resultjson['error_message']=resultjson['error_message']
                    resultjson['userindustryinfo']=np.array(resultjson['userindustryinfo']).tolist()
                    updateServerstate('行业更新',username,'delete')
                    return JsonResponse(resultjson)
               except Exception as e:
                    resultjson={'error_message':'',
                              'serverstate':'',
                              'userindustryinfo':'',
                              }
                    #resultjson['serverstate']='ERROR'
                    updateServerstate('行业更新',username,'delete')
                    resultjson['error_message']=str(e)
                    print(e)
                    return JsonResponse(resultjson)
          else:
               try:
                    myform =industryRollForm(request.POST,(username))
                    
                    if myform.is_valid(): #提供验证判断是否有效，成立则返回是Ture
                         # 表示开始计算
                         # print(settings.BASE_DIR)
                         updateServerstate('行业轮转',username,'add')
                         #serverparams['computerparams']['行业轮转']=1
                         form= request.POST
                         startdate= form.getlist('startdate')[0]
                         enddate=form.getlist('enddate')[0]
                         datasourcetype=form.getlist('sources')[0]
                    
                         dateofnum=form.getlist('numofperiod')[0]
                         periodtype=form.getlist('periodtype')[0]
                         
                         #isall=form.getlist('isall')[0]
                         # 得到处理的函数
                         back_industry=BackTrade_IndustryRoll.industryData()
                         industfilename='行业轮转'
                         for keys in industryprocss.industryprocess.allindustrys_dict.keys():
                              keyname=industryprocss.industryprocess.allindustrys_dict[keys]
                              if datasourcetype==str(keys):
                                   industfilename=industfilename+'-'+str(keyname)
                                   break
                         if periodtype=='all':
                              isall=True
                              industfilename=industfilename+'-所有'
                         elif periodtype=='D':
                              isall=False
                              industfilename=industfilename+'-'+str(dateofnum)+str(periodtype)
                         
                         industfilename=industfilename+'('+startdate+'-'+enddate+')'
                         nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                    
                         industfilename=industfilename+'-'+username+'('+nowtime+').csv'
                         savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                         if isall:
                              maxindustrypd = back_industry.haveIndustryOrConceptData(start_date=startdate, end_date=enddate,
                                                                      
                                                                      industfilename=industfilename,
                                                                      savelocation=savelocation,
                                                                      timeperiod=periodtype,  # 可以在时间段内按照周和月处理，从而在整个时间段看板块变化
                                                                 
                                                                      datasourcetype=datasourcetype)
                              
                              industrydict=request.session.get('industrydict','')
                              
                              if industrydict=='':
                                   industrydict=dict()
                                   industrydict['板块统计-连续']=industfilename
                                   request.session['industrydict']=industrydict
                    
                              else:
                                   industrydict['板块统计-连续']=industfilename
                                   request.session['industrydict']=industrydict
                              # 表示已经计算结束
                              updateServerstate('行业轮转',username,'delete')
                              filename=industfilename
                              filepath = savelocation +industfilename
                              ###########发送邮件 
                              sendbacktraderesult(filepath,username,'板块统计-连续','板块统计','检测结果.csv')
                              return render(request, "pageIndex/industryroll.html",{'form':myform,
                                                                           'username':username,
                                                                           'filename':filename})
                         #return render(request, "pageIndex/industryroll.html",{'form':form,'filename':filename})
                         elif periodtype=='D':
                              sharelistname=[]
                              allconceptnames=form.getlist('datasourenamelist')
                              if len(sharelistname)>=5:
                                   raise RuntimeError('板块个数不能超过5') 
                              result_pd = pd.DataFrame()
                              for listname in allconceptnames:
                                   try:
                                        listname=[str(listname)]
                                        sharelist=havesharelist_fromname(datasourcetype,listname,1)

                                        return_pd = back_industry.haveIndustryOrConceptData(start_date=startdate, end_date=enddate,
                                                                                               datasourcetype=datasourcetype,
                                                                                               industfilename=industfilename,
                                                                                               savelocation=savelocation,
                                                                                               timeperiod=periodtype,
                                                                                               # 可以在时间段内按照周和月处理，从而在整个时间段看板块变化
                                                                                               sharelist=sharelist,
                                                                                               numofperiod=dateofnum,
                                                                                               labelname=listname[0]
                                                                                               )
                                   

                                        if result_pd.size==0:
                                                  result_pd=return_pd
                                        else:
                                                  result_pd=result_pd.merge(return_pd,how='left',left_index=True,right_index=True) 
                                   except Exception as e:
                                             continue                                            
                              if result_pd.size >0:
                                   savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                                   filepath = savelocation +industfilename
                                   result_pd.to_csv(filepath, index=True, encoding='GBK')
                                   industrydict=request.session.get('industrydict','')
                                   if industrydict=='':
                                        industrydict=dict()
                                        industrydict['板块统计-日分']=industfilename
                                        request.session['industrydict']=industrydict
                         
                                   else:
                                        industrydict['板块统计-日分']=industfilename
                                        request.session['industrydict']=industrydict
                                   # 表示已经计算结束
                                   updateServerstate('行业轮转',username,'delete')
                                   #serverparams['computerparams']['行业轮转']=0
                                   filename=industfilename
                                   ###########发送邮件 
                                   sendbacktraderesult(filepath,username,'板块统计-日分','板块统计','检测结果.csv')
                                   return render(request, "pageIndex/industryroll.html",{'form':myform,
                                                                                'username':username,
                                                                                'filename':filename}) 
                              else:
                                   errormessage='没有查到数据,请稍后。。'
                                   updateServerstate('行业轮转',username,'delete')
                                   #serverparams['computerparams']['行业轮转']=0
                                   return render(request, "pageIndex/industryroll.html",{'form':myform,
                                                                                'errormessage':errormessage,
                                                                                'username':username,
                                                                                'filename':''})  
                                                                      
                         
                                                                      
               
                    else:
                         raise RuntimeError()                                    
               except  Exception as  e:
                    errormessage=str(e)
                    updateServerstate('行业轮转',username,'delete')
                    #serverparams['computerparams']['行业轮转']=0
                    return render(request, "pageIndex/industryroll.html",{'form':myform,
                                                       'username':username,
                                                       'filename':'',
                                                       'errormessage':errormessage}) 
                                                 

     else:
          username=request.session.get('username','')
          if not(username ==''):
               if  not (request.is_ajax):
                    form =industryRollForm(request.POST,(username))
                    filename=''
                    return render(request, "pageIndex/industryroll.html",{'form':form,
                                                                       'username':username,
                                                                       'filename':''})  
                
               else:  
                    try:
                         resultjson={'error_message':'',
                         'userindustrylist':'',
                         'factorconditiondict':'',
                         'strongconditiondict':'',
                         'datasoure':dict(),
                         }
                         datasourcevalue=str(request.GET['datasourcevalue'])
                         if datasourcevalue=='addindustrysharecode':
                              sharecode=str(request.GET['sharecode'])
                              industryname=str(request.GET['industryname'])
                              indusprocess=industryprocss.industryprocess()
                              resultstr=indusprocess.addindustrysharecode(username=username,
                                                                           sharecode=sharecode,
                                                                           industryname=industryname)
                              resultjson={'isok':''}
                              resultjson['isok']=resultstr
                              return JsonResponse(resultjson)
                         elif datasourcevalue=='deleteindustrysharecode':
                              sharecode=str(request.GET['sharecode'])
                              industryname=str(request.GET['industryname'])
                              indusprocess=industryprocss.industryprocess()
                              resultstr=indusprocess.deleteindustrysharecode(username=username,
                                                                           sharecode=sharecode,
                                                                           industryname=industryname)

                              resultjson={'isok':''}
                              resultjson['isok']=resultstr
                              return JsonResponse(resultjson)
                         else:

                              alllistname=havealllistname(datasourcevalue)
                              userindustrylist=haveuserindustry_name(username=username)
                              if len(userindustrylist)>0:
                                   resultjson['userindustrylist']=np.array(userindustrylist).tolist()
                              shareconditionsdict,strongconditondict=haveallconditions()
                              

                              if len(alllistname)<=0:
                                   raise RuntimeError('没有找到数据')
                              
                              resultjson['datasoure']=np.array(alllistname).tolist()
                              
                              resultjson['factorconditiondict']=np.array(shareconditionsdict).tolist()
                              resultjson['strongconditiondict']=np.array(strongconditondict).tolist()
                              return JsonResponse(resultjson)
                    except Exception as e:
                         resultjson={'error_message':'',
                         'datasoure':'',
                         'userindustrylist':'',
                         'factorconditiondict':'',
                         'strongconditiondict':'',
                         }
                         resultjson['error_message']=str(e)
                         print(e)
                         return JsonResponse(resultjson)
          else:
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})

def logins(request):
     loginform = LoginForm(request.POST)
     if request.method == "POST": #request是 HttpRequest的对象，利用它的的method属性，判断请求方法。
        username=loginform['username'].data
        userpassword=loginform['usepassword'].data
        isvalid=authenticate(username=username,password=userpassword)
        if isvalid is None:
          error_message='用户名或密码不合法!'
          return render(request, "pageIndex/logins.html",{'form':loginform,'error_message':error_message}) 
        else:
          request.session['username'] = username
          request.session['userpassword']=userpassword
          
          nowdate=str(dt.datetime.now().date())

          request.session['logindate'] =nowdate
          userpath=settings.BASE_DIR+"/static/download/"+username+'/'
          if not (os.path.exists(userpath)):
              os.makedirs(userpath)
          return  render(request, "pageIndex/indexframe.html",{'name':username,'logindate':nowdate})
     else:
          username=request.session.get('username','')
          if not(username ==''):
              
               nowdate=request.session['logindate']
               userpath=settings.BASE_DIR+"/static/download/"+username+'/'
               if not (os.path.exists(userpath)):
                    os.makedirs(userpath)
               return  render(request, "pageIndex/indexframe.html",{'name':username,'logindate':nowdate})   
          else:
               return render(request, "pageIndex/logins.html",{'form':loginform})
def multifactors(request):
     if request.method == "POST":
          username=request.session.get('username','')
          if username =='':
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})
          else:
               if not(request.is_ajax):
                    myform = multifactorsForm(request.POST,(username))

                    try:
                         shareconditionsdict,strongconditondict=haveallconditions()
                         if myform.is_valid(): #提供验证判断是否有效，成立则返回是Ture
                              # 表示开始计算

                              updateServerstate('多维模型',username,'add')
                              #serverparams['computerparams']['多维模型']=1
                              form= request.POST
                              startdate= form.getlist('startdate')[0]
                              enddate=form.getlist('enddate')[0]
                              if enddate < startdate:
                                   raise RuntimeError('结束时间不能小于开始时间!')
          
                              # datasource=form.getlist('sources')[0]
                              # datatypes=form.getlist('typesource')[0]
                              #periodtype=form.getlist('checktype')[0]
                              selectype=form.getlist('selectype')[0]
                              datasourcetype=form.getlist('sources')[0]
                              selectsharelistnames=form.getlist('datasourenamelist')
                              # periodtype=form.getlist('checktype')[0]
                              
                              industfilename='多维模型'
                              isalllistshare=False
                              if len(form.getlist('havealllistshares'))>0:
                                   isalllistshare=True
                         
                              
                              if isalllistshare:
                                   # 用东方财富的代码
                                   # sharelist=havesharealllist()
                                   industfilename=industfilename+'-'+'所有公司'
                              else:
                                  
                                   if len(selectsharelistnames) >5:
                                        raise RuntimeError('板块不能超过5个')
                                   if len(selectsharelistnames) <=0:
                                        raise RuntimeError('需要选择至少1个板块')
                                   industfilename=industfilename+'('
                                   for tempname in selectsharelistnames:
                                        industfilename=industfilename+str(tempname)+'-'
                                   industfilename=industfilename+')'
                              if selectype=='isCo':
                                   sharelist=[]
                                   havedsharecode = BackTrade_ShareByCondition.shareByConditions()
                                   industfilename=industfilename+'-条件选股'
                                   allcoditions=form.getlist('shareconditions')
                                   if len(allcoditions)<=0:
                                        raise RuntimeError('没有选择筛选条件')
                                   conditiondict=dict()
                                   for con in allcoditions:
                                        max_name='max_'+str(con)
                                        min_name='min_'+str(con)
                                        max_value=form.getlist(max_name)[0]
                                        if max_value == 'inf':
                                             max_value= float('inf')
                                        else:
                                             max_value=convertnulltozero(form.getlist(max_name)[0])

                                        min_value=convertnulltozero(form.getlist(min_name)[0])
                                        conditiondict[con]=[min_value, max_value]
                                  
                                   selectedsharelist_pd=pd.DataFrame()
                                    
                                   if isalllistshare:
                                        # 全部代码
                                        sharelist=havesharealllist()
                                   else:
                                        sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=selectsharelistnames)
                                   if startdate==enddate:

                                        selectedsharelist,selectedsharelist_pd = havedsharecode.haveallsharebyconditions_singleday(
                                        codelist=sharelist,
                                        startdate=startdate,
                                        enddate=enddate,
                                        conditiondict=conditiondict)
                                        industfilename=industfilename+'('+enddate+')'
                                   else:
                                        selectedsharelist,selectedsharelist_pd = havedsharecode.haveallsharebyconditions(
                                        codelist=sharelist,
                                        startdate=startdate,
                                        enddate=enddate,
                                        conditiondict=conditiondict)
                                        industfilename=industfilename+'('+startdate+'-'+enddate+')'
                                   #对选出来的股票代码增加必要的信息
                                   if len(selectedsharelist)>0:
                                        addcodelistinfos=havedsharecode.havecodelistinfos(codelist=selectedsharelist)
                                        selectedsharelist_pd=pd.merge(selectedsharelist_pd,addcodelistinfos,how='left',
                                                                      left_on='Symbol',right_on='Symbol')
                                   
                                   ####################################
                                   nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                                   selectcolumns=selectedsharelist_pd.columns
                                   selectedsharelist_pd=np.round(selectedsharelist_pd,5)
                                   selectedsharelist_pd['Symbol']=selectedsharelist_pd['Symbol']+'\t'
                                   selectedsharelist_pd=selectedsharelist_pd.rename(columns={'Symbol':'股票代码'})
                                   con_keys=conditiondict.keys()
                                   for index in range(len(selectcolumns)):
                                        col=selectcolumns[index]
                                        newcol=''
                                        for keyname in shareconditionsdict.keys():
                                             if col==str(keyname):
                                                  newcol= newcol+str(shareconditionsdict[keyname])
                                                  break
                                        for keyname in con_keys:
                                             if col==str(keyname):
                                                  newcol=newcol+str(conditiondict[keyname])
                                                  break
                                        if newcol != '':
                                             selectedsharelist_pd=selectedsharelist_pd.rename(columns={col:newcol})
                                   industfilename=industfilename+'-'+username+'('+nowtime+').csv'
                                   savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                                   factordict=request.session.get('factordict','')
                                   if factordict=='':
                                        factordict=dict()
                                        factordict['多维模型-条件选股']=industfilename
                                        request.session['factordict']=factordict
                                   else:
                                        factordict['多维模型-条件选股']=industfilename
                                        request.session['factordict']=factordict
                                   filepath = savelocation +industfilename
                                   
                                   selectedsharelist_pd.to_csv(filepath, index=False, encoding='GBK')
                                   # 代表计算完成
                                   filename=industfilename
                                   updateServerstate('多维模型',username,'delete')
                                   ###########发送邮件 
                                   sendbacktraderesult(filepath,username,'多维模型-条件选股','因子选股','检测结果.csv')
                                   #serverparams['computerparams']['多维模型']=0
                                   return render(request, "pageIndex/multifactors.html",{'form':myform,
                                                                 'username':username,
                                                                 'filename':filename,
                                                                  
                                                                 'shareconditionsdict':shareconditionsdict,
                                                                 'strongconditondict':strongconditondict})
                              elif selectype=='isSt':
                                   sharelist=[]
                                   havedsharecode = BackTrade_ShareByCondition.shareByConditions()
                                   allcoditions=form.getlist('strongconditions')
                                   if isalllistshare:
                                        # 全部代码
                                        sharelist=havesharealllist()
                                   else:
                                        sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=selectsharelistnames)
                                   industfilename=industfilename+'-动量选股'
                                   if len(allcoditions)<=0:
                                        raise RuntimeError('没有选择动量因子')
                                   
                                   strongcondition = {'longMin': dict(), 'totalRet': dict()}
                                   
                                   historynums = 30
                                   min_long=0
                                   for con in allcoditions:
                                        if str(con)=='longMin':
                                             period_name='period_'+str(con)
                                             gain_name='gain_'+str(con)
                                             period_value=convertnulltozero(form.getlist(period_name)[0])
                                             if period_value<5:
                                                  raise RuntimeError('周期不能小于5')
                                             gain_value=convertnulltozero(form.getlist(gain_name)[0])
                                             if gain_value<0:
                                                  raise RuntimeError('幅度不能小于0')
                                             lastgrowdict=dict()
                                             lastgrowdict['period']=period_value
                                             lastgrowdict['gain']=gain_value
                                             strongcondition['longMin']=lastgrowdict
                                        elif str(con)=='totalRet':
                                             period_name='period_'+str(con)
                                             gain_name='gain_'+str(con)
                                             period_value=convertnulltozero(form.getlist(period_name)[0])
                                             if period_value<5:
                                                  raise RuntimeError('周期不能小于5')
                                             gain_value=convertnulltozero(form.getlist(gain_name)[0])
                                             if gain_value<0:
                                                  raise RuntimeError('幅度不能小于0')
                                             stogrowdict=dict()
                                             stogrowdict['period']=period_value
                                             stogrowdict['gain']=gain_value
                                             strongcondition['totalRet']=stogrowdict
                                        
                                   strongcode_dict = havedsharecode.havestrongsharecode(codelist=sharelist,startdate=startdate,
                                                            enddate=enddate,
                                                            strongcondition=strongcondition,

                                                            historynums=historynums,
                                                            min_long=min_long
                                                            )
                                   
                                   industfilename=industfilename+'('+startdate+'-'+enddate+')'
                                   nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
          
                                   industfilename=industfilename+'-'+username+'('+nowtime+').xlsx'
                                   savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                                   
                                   filepath = savelocation +industfilename
                                   con_keys=strongconditondict.keys()
                                   with pd.ExcelWriter(filepath) as writer:
     
                                        for keys in strongcondition.keys():
                                             if len(strongcondition[keys])==0:
                                                  continue
                                             temp_pd=strongcode_dict[str(keys)]
                                             temp_pd['股票代码']=temp_pd['股票代码']+'\t'
                                             sheetname=str(keys)
                                             for keyname in con_keys:
                                                  if str(keys)==str(keyname):  
                                                       sheetname=str(strongconditondict[keyname])+'(周期|'+str(strongcondition[keys]['period'])+'幅度|'+str(strongcondition[keys]['gain'])+")"
                                             temp_pd.to_excel(writer, index=False,sheet_name=sheetname,engine='openpyxl')
                                   
                                   # 代表计算完成
                                   #serverparams['computerparams']['多维模型']=0
                                   updateServerstate('多维模型',username,'delete')
                                   factordict=request.session.get('factordict','')
                                   if factordict=='':
                                        factordict=dict()
                                        factordict['多维模型-动量选股']=industfilename
                                        request.session['factordict']=factordict
                                   else:
                                        factordict['多维模型-动量选股']=industfilename
                                        request.session['factordict']=factordict
                                   filename=industfilename
                                   ###########发送邮件 
                                   sendbacktraderesult(filepath,username,'多维模型-动量选股','因子选股','检测结果.csv')
                                   return render(request, "pageIndex/multifactors.html",{'form':myform,
                                                                 'username':username,
                                                                 'filename':filename,
               
                                                                 'shareconditionsdict':shareconditionsdict,
                                                                 'strongconditondict':strongconditondict})
                              elif selectype=='isfama':
                                   sharelist=[]
                                   factorstype=form.getlist('facotrstype')[0]
                                   if factorstype=='isthree':
                                        factorstype=3
                                   elif factorstype=='isfour':
                                        factorstype=4
                                   elif factorstype=='isfive':
                                        factorstype=5
                                   industfilename=industfilename+'-'+str(factorstype)+'因子选股(市场低估)-'
                                   freerate=0.01
                                   numofreturn=10 # 默认返回10个代码
                                   havedsharecode=BackTrade_ShareChoiceByFactors.sharechoice()
                                   
                                   lowsharecode_pd=pd.DataFrame()
                                   for listname in selectsharelistnames:
                                        listname_app=[str(listname)]
                                        sharelist=havesharelist_fromname(datasource=datasourcetype,sharelistname=listname_app)
                                        isdeletelowcorrlist=False
                                        if len(form.getlist('isdeletelowcorrlist'))>0:
                                             isdeletelowcorrlist=True
                                        # 只有选择1个模块的时候才筛选
                                        isdeletelowcorrlist=False
                                        if isdeletelowcorrlist:
                                            
                                             corr_sd=convertnulltozero(form.getlist('corr_sd')[0])
                                             if (corr_sd) <= 0 or(corr_sd >=1):
                                                  raise RuntimeError('筛选标准要0~1')
                                             from  fu_t1.BackTrade_Factors import FactorsTest
                                             factTest = FactorsTest(start_date=startdate, end_date=enddate)
                                             method='corr'
                                             result_pd = factTest.shareCorrlattionT1_inner(sharecodelist=sharelist,
                                                            start_date=startdate,
                                                            end_date=enddate,
                                                            groupcode=sharelist,
                                                            method=method, grouptype = 'isinnergroup')
                                             result_pd = result_pd[result_pd['相关系数'] > corr_sd]
                                             concept_cons_em_df = result_pd['股票代码'].drop_duplicates().tolist()
                                             for countindex in range(len(concept_cons_em_df)):
                                                  concept_cons_em_df[countindex] = str(concept_cons_em_df[countindex]).split()[0]
                                             sharelist=concept_cons_em_df
                                        lowpricecode_byliquid, lowpricecode_bymkarket = havedsharecode.havelowpricecode(
                                             codelist=sharelist,
                                             startdate=startdate,
                                             currentdate=enddate,
                                             enddate=enddate,
                                             grouptype=1,  # 组合分组类型，1 代表2*3 2=2*2 3=2*2*2*2
                                             numofreturn=numofreturn,  # 返回多少个股票，默认返回5个
                                             factorstype=factorstype)
                                        columns1 = (listname + '_流动市值')
                                        columns2 = (listname + '_总市值')
                                        lowsharecode_temp = pd.DataFrame(columns=[columns1, columns2], index=range(numofreturn))
                                        len_byliquid = len(lowpricecode_byliquid)
                                        if len_byliquid > 0:
                                             lowpricecode_byliquid = lowpricecode_byliquid + '\t'
                                        if len_byliquid < numofreturn:
                                             nullen = numofreturn - len_byliquid
                                             nullen_list = ['' for x in range(nullen)]
                                             lowpricecode_byliquid = np.append(lowpricecode_byliquid, nullen_list)

                                        len_bymarket = len(lowpricecode_bymkarket)
                                        if len_bymarket > 0:
                                             lowpricecode_bymkarket = lowpricecode_bymkarket + '\t'
                                        if len_bymarket < numofreturn:
                                             nullen = numofreturn - len_bymarket
                                             nullen_list = ['' for x in range(nullen)]
                                             lowpricecode_bymkarket = np.append(lowpricecode_bymkarket, nullen_list)

                                        lowsharecode_temp.loc[:, columns1] = lowpricecode_byliquid
                                        lowsharecode_temp.loc[:, columns2] = lowpricecode_bymkarket
                                        if len(lowsharecode_pd.columns) == 0:
                                             lowsharecode_pd = lowsharecode_temp
                                        else:
                                             lowsharecode_pd = lowsharecode_pd.merge(lowsharecode_temp, how='outer', left_index=True,
                                                                                     right_index=True)

                                   industfilename=industfilename+'('+startdate+'-'+enddate+')'
                                   nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
                              
                                   industfilename=industfilename+'-'+username+'('+nowtime+').xls'
                                   savelocation=settings.BASE_DIR+"/static/download/"+username+'/'
                                   filepath = savelocation +industfilename
                                   factordict=request.session.get('factordict','')
                                   if factordict=='':
                                        factordict=dict()
                                        factordict['多维模型-因子选股']=industfilename
                                        request.session['factordict']=factordict
                                   else:
                                        factordict['多维模型-因子选股']=industfilename
                                        request.session['factordict']=factordict
                                   lowsharecode_pd.to_csv(filepath, index=False, encoding='GBK')
                                   filename=industfilename
                                   ###########发送邮件 
                                   sendbacktraderesult(filepath,username,'多维模型-fama选股','因子选股','检测结果.csv')
                                   updateServerstate('多维模型',username,'delete')
                                   #serverparams['computerparams']['多维模型']=0
                                   return render(request, "pageIndex/multifactors.html",{'form':myform,
                                                                 'username':username,
                                                                 'filename':filename,
                                                                  
                                                                 'shareconditionsdict':shareconditionsdict,
                                                                 'strongconditondict':strongconditondict})
                              elif selectype=='istechindex':

                                  raise RuntimeError('技术指标未开放！')   
                              else:
                                updateServerstate('多维模型',username,'delete')
                                raise RuntimeError('类型错误')   

                         else:
                               raise RuntimeError()
                    except Exception as e:
                         print(e)
                         errormessage=str(e)
                         # 表示已经计算结束,确保还可以继续计算
                         updateServerstate('多维模型',username,'delete')
                         #serverparams['computerparams']['多维模型']=0
                         return render(request, "pageIndex/multifactors.html",{'form':myform,
                                                            'filename':'',
                                                            'errormessage':errormessage,
                                                            'username':username })  
               else:
                    try:
                         #serverparams['computerparams']['多维模型']=0
                         updateServerstate('多维模型',username,'delete')
                         resultjson={'error_message':'',
                                   
                                     'resultinfo':'',
                                    }
                         return JsonResponse(resultjson)
                    except Exception as e:
                         updateServerstate('多维模型',username,'delete')
                         #serverparams['computerparams']['多维模型']=0
                         resultjson={'error_message':'',
                                   
                                    'resultinfo':'ERROR',
                                    }
                         resultjson['error_message']=str(e)
                         print(e)
                         return JsonResponse(resultjson)

     else:
          username=request.session.get('username','')
          if not(username ==''):
               myform = multifactorsForm(request.POST,(username))
               if not(request.is_ajax):
                    shareconditionsdict,strongconditondict= haveallconditions()
                    
                    return render(request, "pageIndex/multifactors.html",{'form':myform,
                                                                           'username':username,
                                                                           'filename':'',
                                                                           'shareconditionsdict':shareconditionsdict,
                                                                           'strongconditondict':strongconditondict})
               else:
                    try:
                         
                         datatype=str(request.GET['datatype'])
                         if datatype=='havetechindexinfo':
                              resultjson={'error_message':'',
                         
                                        'techindex':dict()
                                        }
                              indexconditiondict=haveindexconditions()           
                              resultjson['techindex']=np.array(indexconditiondict).tolist()
                         
                              return JsonResponse(resultjson)
                         elif datatype=='datasource':
                              datasourcevalue=str(request.GET['datasourcevalue'])
                              resultjson={'error_message':'',
                         
                                        'datasoure':dict()
                                        }
                              alllistname=havealllistname(datasourcevalue)
                              
                              shareconditionsdict,strongconditondict=haveallconditions()
                              

                              if len(alllistname)<=0:
                                   raise RuntimeError('没有找到数据')
                              
                              resultjson['datasoure']=np.array(alllistname).tolist()
                         
                              return JsonResponse(resultjson)
                    except Exception as e:
                         resultjson={'error_message':'',
                         'datasoure':'',
                        
                         }
                         resultjson['error_message']=str(e)
                         print(e)
                         return JsonResponse(resultjson)
               
          else:
               logins=LoginForm(request.POST)
               return render(request, "pageIndex/logins.html",{'form':logins})
def havebacktradeinfos(request):
     username=request.session.get('username','')
     
     grant_userlist=np.union1d(views.adminuserslist,views.upuserslist)
     grant_userlist=np.union1d(grant_userlist,views.genuserslist)
     if (username not in grant_userlist):
          logins=LoginForm(request)
          return render(request, "pageIndex/logins.html",{'form':logins}) 
     else:
        try:
          if(request.is_ajax): 
               import fu_t1.BackTrade_MultiShareStrategy as BackTrade_MultiShareStrategy
               datatype=str(request.GET['datatype'])
               if datatype=='havebacktradeinfos':
                    resultjson={'result_info':0,
                                   'btinfos':'',
                                   'error_message':''}
                    trategyvalue=str(request.GET['trategyname']) 
                    try:
                         tragedylist_dict=BackTrade_MultiShareStrategy.tragedylistdict
                         for keyvalue in tragedylist_dict.keys():
                              if str(keyvalue)==trategyvalue:
                                   btinfos =tragedylist_dict[keyvalue].rd_bt_infos()
                                   
                                   if len(btinfos)>0:
                                        # btinfos.sort(reverse=True)
                                        # #显示最新的120条数据
                                        # btinfos=btinfos[0:120]
                                        showinfos=btinfos
                                        showinfos.sort(reverse=False)
                                        # len_tol=len(showinfos)
                                        # if len_tol >120:
                                        #      # mod_num=int(len_tol/120)
                                        #      showinfos[len_tol-120:len_tol]
                                        resultjson['btinfos']=np.array(showinfos).tolist()
                         return JsonResponse(resultjson)
                    except: 
                         return JsonResponse(resultjson)
                         
                    
                         
               elif datatype=='clearbacktradeinfos':
                    resultjson={'result_info':0,
                                   'btinfos':'',
                                   'error_message':''}
                    trategyvalue=str(request.GET['trategyname']) 
                    tragedylist_dict=BackTrade_MultiShareStrategy.tragedylistdict
                    try:
                         for keyvalue in tragedylist_dict.keys():
                              if str(keyvalue)==trategyvalue:
                                   tragedylist_dict[keyvalue].cl_bt_infos()
                                   tragedylist_dict[keyvalue].set_cons({},{},{})
                         
                         return JsonResponse(resultjson)
                    except:
                         return JsonResponse(resultjson)
               else:
                    raise RuntimeError('参数有误')
        except Exception as e:
          resultjson={'result_info':0,
                    'btinfos':'',
                    'error_message':''}
          resultjson['error_message']=str(e)
          return JsonResponse(resultjson)
def pageindex(request):
     username=request.session.get('username','')
     if not(username ==''):
         
              
               #return  render(request, "pageindex.html",{'name':username,'logindate':nowdate}) 
          if(request.is_ajax): 
               request.session.flush()
               resultjson={'result_info':0,
                          
                         'error_message':''}
               resultjson['result_info']='ok'
               return JsonResponse(resultjson)
          else:
               nowdate=request.session['logindate']
               return  render(request, "pageIndex/pageindex.html",{'name':username,'logindate':nowdate})  
               
     else:
          loginform = LoginForm(request.POST)
          return render(request, "pageIndex/logins.html",{'form':loginform})

def sendbacktraderesult(filepath,username,content,subject,filesendname):
        import fu_t1.BackTrade_postmail as BackTrade_postmail 
        from django.contrib.auth.models import User
        nowtime=dt.datetime.today().strftime('%Y-%m-%d-%H%M%S')
        ############开始发送文件
        try:
            mailManager =BackTrade_postmail.MailManager() 
            # mail = mailManager.retrMail() 
            # if mail != None: 
            #      print(mail)
            toaddress=User.objects.get(username=username).email
            # if toaddress=='280114939@qq.com':
            #     toaddress='lj340111@sina.com'
            mail_content=username+'-'+content+'-'+'-'+str(nowtime)+':'+'本次回测结果'
            mailManager.sendMsg(mail_subject=subject,mail_content=mail_content,
                                    toaddress=toaddress,filepath=filepath,filesendname=filesendname)
        except Exception as e:
            print(e)
            
        
def filedownload(request,usename, filename):
    try:
        
        print(settings.BASE_DIR)
        savelocation=settings.BASE_DIR+"/static/download/"+usename+'/'
        filepath=savelocation+filename

        response = FileResponse(open(filepath, 'rb'))
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = 'attachment; filename=' + filepath
        return response
    except Exception as e:
        print(e)
        raise Http404
def showbackfigure(request,filename):
    try:
        
        print(settings.BASE_DIR)
        savelocation=settings.BASE_DIR+'/templates/pageIndex/'
        allfilename='static/'+filename
        
        filepath=savelocation+allfilename

        
        return render(request, filepath)
    except Exception as e:
        print(e)
        raise Http404
def havealllistname(strconceptname=''):
     ini_index=str(strconceptname).find('_self_user_industry')
     if ini_index>=0:
          username=str(strconceptname)[0:ini_index]
          alllistname=haveuserindustry_name(username=username)
          return  alllistname
     else:
         
          strconceptname=strconceptname+'_name'
          initcal =industryprocss.industryprocess()
          listdir_method = dir(initcal)
          
          try:
               for templist in listdir_method:
               
                    if (str(templist).find(strconceptname))>0:
                         
                         return   eval('initcal.' + str(templist) + '()')
                    
          except Exception as e:
               print(e)
               print('没有找到对应方法,返回空')
               return []
def havealllist():
        #返回所有行业和概念列表  
          filepath=settings.BASE_DIR+'/savefilepath/'
          # 同花顺行业
          allConceptshare=pd.read_csv(filepath+'同花顺行业.csv',encoding='gb2312')
          allthsindustrylist = allConceptshare['板块名称'].values
          
           # 同花顺概念
          allConceptshare=pd.read_csv(filepath+'同花顺概念.csv',encoding='gb2312')
          allthsconceptlist = allConceptshare['板块名称'].values

           # 东方财富行业
          allConceptshare=pd.read_csv(filepath+'东方财富行业.csv',encoding='gb2312')
          allemsindustrylist = allConceptshare['板块名称'].values

           # 东方财富概念
          allConceptshare=pd.read_csv(filepath+'东方财富概念.csv',encoding='GBK')
          allemsconceptlist = allConceptshare['板块名称'].values

          return allthsindustrylist,allthsconceptlist,allemsindustrylist,allemsconceptlist
def haveconditionlist():
     tradeconditionsdict = {
                'volume':'交易量',  # 当天的收益率
                # 'close': [0, 0],  # 当天的收盘价格
               'marketvalue': '市值',  # 企业市场价值
                #"free_share_ratio": '自由股本',  # 自由股本
                'vol_change': '交易量变化',  # 交易量变化
                 'pe':'市盈率',  # 滚动市盈率
                'turnover': '换手率',  # 换手率
                'ps': '市销率',  # 滚动市销率
                'pb': '市净率',  # 滚动市净率
               'price_change_ratio': '价格变化',  # 每个bar价格的最大变化比例，(high-low)/low
               
                #   'free_share_ratio':'自由股本比',
            }
     financeconditionsdict ={ 
                # 公司指标
                'total_asset': '总资产',  # 总资产
                'total_debt': '总负债',  # 总负债
                # 发展能力指标
                'net_Profit_growth': ' 净利润增长',  # 净利润增长
                'Research_ratio': '研发投入比例',  # 研发投入比例
                # 盈利能力指标
                'ROE': 'ROE',#[0.5, float('inf')],  # 滚动ROE
                'solid_growth': '固定资产增长',  #固定资产增长
                'trade_profit': '营业毛利率',  # 营业毛利率
                # 风险指标
               'liquid_ratio': '流动比率',  # 公司流动比率
                'interest_ratio':'利息倍数',
                'debtratio':'负债比例',
                # 相对价值指标
                 'EVRatio': '价值倍数',  # 企业价值倍数
                # 股东指标
                'institute_ratio': '机构持股比例',  # 机构持股比例
               #  # 管理指标
               #  'Gov_index':'公司治理指数',  # 公司治理指数
          }
     return tradeconditionsdict,financeconditionsdict
# 得到选中的sharelist 和sharelistname和过程信息
def havesharelist(form,numofgroups):
     datasource=form.getlist('sources')[0]
     datatypes=form.getlist('typesource')[0]
     if datasource=='isEms':
          isEms= True
          isThs=False
     elif datasource=='isThs':
          isEms= False
          isThs=True
     if datatypes=='isIndustry':
          isIndustry=True
          isConcept=False
     elif datatypes=='isConcept':
          isIndustry=False
          isConcept=True  
     errormessage=''   
     sharelist=[]
     sharelistname=[]           
     if numofgroups==1:
          if isEms:
               if isIndustry:
                    sharelistname=form.getlist('emsindustry')
                    if len(sharelistname)!=1:
                         errormessage='需要选择东方财富1个行业板块'
                    else:
                         strname=sharelistname[0]
                         sharelist= ak.stock_board_industry_cons_em(symbol=strname)['代码'].tolist()

               else:
                    sharelistname=form.getlist('emsconcept')
                    if len(sharelistname)!=1:
                         errormessage='需要选择东方财富1个概念板块'
                    else:
                         strname=sharelistname[0]
                         sharelist= ak.stock_board_concept_cons_em(symbol=strname)['代码'].tolist()
          elif isThs:
                    if isIndustry:
                         sharelistname=form.getlist('thsindustry')
                         if len(sharelistname)!=1:
                              errormessage='需要选择同花顺1个行业'
                         else:
                              strname=sharelistname[0]
                              sharelist= ak.stock_board_industry_cons_ths(symbol=strname)['代码'].tolist()
                         
                    else:
                         sharelistname=form.getlist('thsconcept')
                         if len(sharelistname)!=1:
                              errormessage='需要选择同花顺概念'
                         else:
                              strname=sharelistname[0]
                              sharelist= ak.stock_board_concept_cons_ths(symbol=strname)['代码'].tolist()
     elif numofgroups > 1:
          if isEms:
               if isIndustry:
                    sharelistname=form.getlist('emsindustry')
                    if len(sharelistname)==0:
                         errormessage='需要选择东方财富行业板块'
                    else:
                         for symbol in sharelistname:
                              templist=ak.stock_board_industry_cons_em(symbol=symbol)['代码'].tolist()
                              sharelist=np.union1d(templist, sharelist) 

               else:
                    sharelistname=form.getlist('emsconcept')
                    if len(sharelistname)==0:
                         errormessage='需要选择东方财富概念板块'
                    else:
                         for symbol in sharelistname:
                              templist=ak.stock_board_concept_cons_em(symbol=symbol)['代码'].tolist()
                              sharelist =np.union1d(templist, sharelist)
          elif isThs:
               if isIndustry:
                    sharelistname=form.getlist('thsindustry')
                    if len(sharelistname)==0:
                         errormessage='需要选择同花顺行业板块'
                    else:
                         for symbol in sharelistname:
                              templist= ak.stock_board_industry_cons_ths(symbol=symbol)['代码'].tolist()
                              sharelist =np.union1d(templist, sharelist)
                                                                                
               else:
                    sharelistname=form.getlist('thsconcept')
               if len(sharelistname)==0:
                    errormessage='需要选择同花顺概念板块'
               else:
                    for symbol in sharelistname:
                         templist= ak.stock_board_concept_cons_ths(symbol=symbol)['代码'].tolist()
                         sharelist =np.union1d(templist, sharelist)
     return sharelist,sharelistname,errormessage
def haveallconditions():
     shareconditionsdict= {
           # 公司指标
                'total_asset': '总资产',  # 总资产
                'total_debt': '总负债',  # 总负债
                'marketvalue': '市值',# [0, float('inf')],  # 市值，在一定时间的均值
                'volume':'交易量', #[0, 0],  # 交易量，两个值代表上下限 在一定时间的均值
                'pe':'市盈率',# [0, 50],  # 滚动市盈率在一定的均值，
                'turnover': '换手率',#[2, 50],  # 换手率
                'ps': '市销率',#[0, 200],  # 滚动市销率
                'pb': '市净率',#[0, 200],  # 滚动市净率
                'ROE': 'ROE',#[0.5, float('inf')],  # 滚动ROE
                'EVRatio': '价值倍数',#[0, 0],  # 企业价值倍数
                'cumReturn': '累计收益',#[0, 0.5]  # 公司的累计收益率，是比例
                'price_change_ratio': '价格变化(H/L)',
                'vol_change': '交易量变化(V/M(5))',  # 交易量变化
                 'turnover_ratio': '换手率变化(V/M(5))',# 换手率变化
                 'Research_ratio': '研发投入比例',  # 研发投入比例
               #   'volume_ratio':'量比',
               #   'free_share_ratio':'自由股本比',
                 'institute_ratio': '机构持股',
                 'net_Profit_growth': ' 净利润增长',  # 净利润增长
                 'trade_profit': '营业毛利率',  # 营业毛利率
                 'debtratio': '负债比',  # 负债比
                 'interest_ratio':'利息倍数',
                 'liquid_ratio': '流动比率',  # 公司流动比率
            }
     strongconditondict={
          'longMin':'连续增长',
          'totalRet':'短期涨幅'
     }
     return shareconditionsdict,strongconditondict
def havetradeconditions():
     tradeconditiondict = {
                'volume':'交易量',  # 当天的收益率
                # 'close': [0, 0],  # 当天的收盘价格
                'marketvalue': '市值',  # 企业市场价值
                #"free_share_ratio": '自由股本',  # 自由股本
                'vol_change': '交易量变化(V/M(5))',  # 交易量变化
                 'pe':'市盈率',  # 滚动市盈率
                'turnover': '换手率',  # 换手率
                'ps': '市销率',  # 滚动市销率
                'pb': '市净率',  # 滚动市净率
                'turnover_ratio': '换手率变化(V/M(5))',  # 每个周期换手率的变化，(high-low)/low
               
                #   'free_share_ratio':'自由股本比',
            }
     return tradeconditiondict
#专门用作参数优化的使用
def havefactorsconditions():
     factorsconditiondict = {
                'volume':'交易量',  # 当天的收益率
                # 'close': [0, 0],  # 当天的收盘价格
                'marketvalue': '市值',  # 企业市场价值
                #"free_share_ratio": '自由股本',  # 自由股本
                'vol_change': '交易量变化(V/M(5))',  # 交易量变化
                 'pe':'市盈率',  # 滚动市盈率
                'turnover': '换手率',  # 换手率

                'ps': '市销率',  # 滚动市销率
                'pb': '市净率',  # 滚动市净率
                'turnover_ratio': '换手率变化(V/M(5))',  # 每个周期换手率的变化，(high-low)/low
                'price_change_ratio':'价格最大变化比率'
                #   'free_share_ratio':'自由股本比',
            }
     return factorsconditiondict
##估值参数
def haveassessvaluefina():
     financeconditiondict ={ 
                # 公司指标
                'total_asset': '总资产',  # 总资产
                'total_debt': '总负债',  # 总负债
                # 发展能力指标
                'net_Profit_growth': ' 净利润增长',  # 净利润增长
                'Research_ratio': '研发投入比例',  # 研发投入比例
                # 盈利能力指标
                'ROE': 'ROE',#[0.5, float('inf')],  # 滚动ROE
                'solid_growth': '固定资产增长',  #固定资产增长
                'trade_profit': '营业毛利率',  # 营业毛利率
                # 风险指标
               'liquid_ratio': '流动比率',  # 公司流动比率
                'interest_ratio':'利息倍数',
                'debtratio':'负债比例',
                # 相对价值指标
               #   'EVRatio': '价值倍数',  # 企业价值倍数
                # 股东指标
                'institute_ratio': '机构持股比例',  # 机构持股比例
               #  # 管理指标
               #  'Gov_index':'公司治理指数',  # 公司治理指数
          }
     return financeconditiondict
def havefinanceconditions():
     financeconditiondict ={ 
                # 公司指标
                'total_asset': '总资产',  # 总资产
                'total_debt': '总负债',  # 总负债
                # 发展能力指标
                'net_Profit_growth': ' 净利润增长',  # 净利润增长
                'Research_ratio': '研发投入比例',  # 研发投入比例
                # 盈利能力指标
                'ROE': 'ROE',#[0.5, float('inf')],  # 滚动ROE
                'solid_growth': '固定资产增长',  #固定资产增长
                'trade_profit': '营业毛利率',  # 营业毛利率
                # 风险指标
               'liquid_ratio': '流动比率',  # 公司流动比率
                'interest_ratio':'利息倍数',
                'debtratio':'负债比例',
                # 相对价值指标
                # 'EVRatio': '价值倍数',  # 企业价值倍数
                # 股东指标
                'institute_ratio': '机构持股比例',  # 机构持股比例
               #  # 管理指标
               #  'Gov_index':'公司治理指数',  # 公司治理指数
          }
     return financeconditiondict
def haveindexconditions():
     indexconditiondict={
     'RSI':['相对强弱',{'key':'RSI','P1':20,'sellpoint':70,'buypoint':30,
                    'buykey':'rsi<= buypoint',
                    'sellkey':'rsi >= sellpoint',
                    'note':'RSI(N日) = (N日内收盘涨幅之和)/(N日内收盘涨跌幅绝对值之和)'}],
     'MACD':['异同平滑',{'key':'MACD','SHORT':12,'LONG':26,'MID':9,'sellpoint':0,'buypoint':0,
                    'buykey':'(diff>dea+ buypoint*dea) and  (diff>0) and (dea>0)' ,
                    'sellkey':'(diff< dea- sellsignal*dea)  and (diff<0) and (dea<0)',
                    'note':'diff =short-long dea=ema(diff,m)'}],
     'MEAN':['均值交叉',{'key':'MEAN','SHORT':5,'LONG':20,'sellpoint':0,'buypoint':0,
                     'buykey':'short>long+long*buypoint',
                     'sellkey':'short<long-long*sellpoint'}],
     'KDJ':['随机指标',{'key':'KDJ','P1':9,'M1':3,'M2':3,'sellpoint':0,'buypoint':0,
                    'buykey':' K > D+ buysignal*D:',
                     'sellkey':' K< D - sellsignal*D',
                     'note':'RSV = (CLOSE - LLV(LOW, P1))/(HHV(HIGH, P1) - LLV(LOW, P1)),\
                      K = EMA(RSV, (M1 * 2 - 1)),D = EMA(K, (M2 * 2 - 1))'
                     }],
     'PriceChange':['价格动量',{'key':'PriceChange','upratio':0.05,'sellpoint':0.05,'buypoint':0.05,
                            'buykey':'cumRatio>=upratio and close >open+open*buypoint',
                            'sellkey':'cumRatio>=upratio and close < open+open*sellpoint',
                            'note':'cumRatio=(high-low)/low,upratio=0.5'}],
     'BOLL':['布尔通道',{'key':'BOLL','P1':5,'S':2,'sellpoint':0,'buypoint':0,
                            'buykey':'close>upperband+upperband*sellpoint',
                            'sellkey':'close<lowerband-lowerband*buypoint',
                            'note':'MID = MA(CLOSE, P1);UPPER = MID + STD(CLOSE, p1) * S,\
                            LOWER = MID - STD(CLOSE, p1) * S'}],
     }
     return indexconditiondict
def havefigureindexconditions():
     indexconditiondict={
     'RSI':['相对强弱',{'key':'RSI','P1':6,'sellsignal':70,'buysignal':30}],
     'MACD':['异同平滑',{'key':'MACD','SHORT':12,'LONG':26,'MID':9,'sellsignal':0,'buysignal':0}],
     'MEAN':['均值交叉',{'key':'MEAN','SHORT':5,'LONG':20,'sellsignal':0,'buysignal':0}],
     'KDJ':['随机指标',{'key':'KDJ','P1':9,'M1':3,'M2':3,'sellsignal':0,'buysignal':0}],
     'Bias':['乖离率',{'key':'Bias','L1':5,'sellsignal':0,'buysignal':0}],
     'BOLL':['布尔通道',{'key':'BOLL','P1':5,'S':2,'sellsignal':0,'buysignal':0}]
     }
     return indexconditiondict

def havesharelist_fromname(datasource='',sharelistname=[], numofname=1):
     #从指定的板块名称中得到所有的股票
     ini_index=str(datasource).find('_self_user_industry')
     if type(sharelistname)==str:
         raise RuntimeError('板块类型需要是列表')
     if ini_index>=0:
          username=str(datasource)[0:ini_index]
          allselflist=haveuserindustry_list(username=username,conceptname=sharelistname)

          return  allselflist
     else:
          datasource=datasource+'_list'
          initcal =industryprocss.industryprocess()
          listdir_method = dir(initcal)
          
          try:
              
               for templist in listdir_method:
               
                    if (str(templist).find(datasource))>0:
                         totallist=[]
                         
                         for sharename in sharelistname:
                              conceptname=sharename
                              sharelist=   eval('initcal.' + str(templist) + '(conceptname)')
                              totallist=np.union1d(totallist, sharelist) 
                         return totallist
                    
          except Exception as e:
               print(e)
               print('没有找到对应方法,返回空')
               return []
def havebacktradeconditions():
     shareconditionsdict= {
           # 公司指标
                
                'marketvalue': '市值',# [0, float('inf')],  # 市值，在一定时间的均值
                'volume':'交易量', #[0, 0],  # 交易量，两个值代表上下限 在一定时间的均值
                'pe':'市盈率',# [0, 50],  # 滚动市盈率在一定的均值，
                'turnover': '换手率',#[2, 50],  # 换手率
                'ps': '市销率',#[0, 200],  # 滚动市销率
                'pb': '市净率',#[0, 200],  # 滚动市净率
                
                'cumReturn': '累计收益',#[0, 0.5]  # 公司的累计收益率，是比例
                'price_change_ratio': '价格变化(H/L)',
                'vol_change': '交易量变化(V/M(5))',  # 交易量变化
                 'turnover_ratio': '换手率变化(V/M(5))',# 换手率变化
               #  'volume_ratio':'量比',
               #  'free_share_ratio':'自由股本比',
                 
            }
     strongconditondict={
          'longMin':'连续增长',
          'totalRet':'短期涨幅'
     }
     return shareconditionsdict,strongconditondict
# 获得所有股票代码
def havesharealllist():
     indusprocc=industryprocss.industryprocess()
     return  indusprocc.have_allshare_list()
# 按照类别选择需要的股票列表
def haveselectalllist(sharealllist=[],sharecodetype=''):
     selectalllist=[]
     if sharecodetype =='isSH_A':
          startcodelist=['600','601','603']
          for tempcode in sharealllist:
               startcode_str=str(tempcode)[0:3]
               if startcode_str in startcodelist:
                    selectalllist.append(tempcode)
     elif sharecodetype =='isSH_S':
          startcodelist=['68']
          for tempcode in sharealllist:
               startcode_str=str(tempcode)[0:2]
               if startcode_str in startcodelist:
                    selectalllist.append(tempcode)
     elif sharecodetype =='isSZ_A':
          startcodelist=['000','001']
          for tempcode in sharealllist:
               startcode_str=str(tempcode)[0:3]
               if startcode_str in startcodelist:
                    selectalllist.append(tempcode)
     elif sharecodetype =='isSZ_C':
          startcodelist=['300','301']
          for tempcode in sharealllist:
               startcode_str=str(tempcode)[0:3]
               if startcode_str in startcodelist:
                    selectalllist.append(tempcode)
     elif sharecodetype =='isSZ_M':
          startcodelist=['002']
          for tempcode in sharealllist:
               startcode_str=str(tempcode)[0:3]
               if startcode_str in startcodelist:
                    selectalllist.append(tempcode)
     return selectalllist
def haveuserindustry_name(username=''):
     indusprocc=industryprocss.industryprocess()
     return indusprocc.have_self_user_name(username)
def haveuserindustry_list(username='',conceptname=[]):
     indusprocc=industryprocss.industryprocess()
     return indusprocc.have_self_user_list(username=username,conceptname=conceptname)

def haveallmachineindex():
     machineindex={'ols':['线性模型',{'kfold':5,'trainoftotal':30,'splitoftest':0.4}],
                    'classreg':['分类模型',{'kfold':5,'trainoftotal':30,'splitoftest':0.4,'alpha':1e-1}],
                    'svm':['支持向量机',{'kfold':5,'trainoftotal':30,'splitoftest':0.4,
                    'kernel':['linear', 'rbf', 'sigmoid', 'poly'],'C':1e-3,'gamma':1e-3}],
                    'rtree':['随机森林',{'kfold':5,'trainoftotal':30,'splitoftest':0.4,
                          'criterion':['gini', 'entropy'],'max_features':['sqrt', 'log2'],'n_estimators':170}],
                    'neuralnetwork':['神经网络',{'kfold':5,'trainoftotal':30,
                    'splitoftest':0.4,'solver':['lbfgs', 'sgd', 'adam'],'activation':['identity', 'logistic', 'tanh', 'relu'],
                    'max_iter':[1000],'alpha':1e-3,'hidden_layer_sizes':80}]
                    } 
     return   machineindex  

     
     

     