#!/usr/bin/env python
# coding: utf-8

# In[1]:


import selenium 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


from numpy import dot
from numpy.linalg import norm

import random
from time import sleep
import pandas as pd
import numpy as np
from tqdm import tqdm
from tqdm import tqdm_notebook

import pickle
from random import randint
from bs4 import BeautifulSoup as bs

import requests
import lxml.html
import re
import os

from konlpy.tag import *
from gensim.models import Word2Vec, FastText


# In[3]:


# 파일 생성 함수
def file_write(df,name):
    
    t = pd.Timestamp.now()
    fname = str(name) + str(t.month) + str(t.day) + ".csv"
    
    print(str(name) + '파일 생성 | 이름 : ' + str(fname))

    df.to_csv(fname,index=False)


# In[16]:


# 특수문자 제거
def cleanText(readData):
    text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', ' ', readData) # 특문제거
    return text


# In[24]:


def get_embedding_vector(model,corpus):
    
    embeding_dict={}
    embeding_df=pd.DataFrame()
    for w,v in zip(model.wv.index2word , model.wv.vectors):
        embeding_dict[w]=v
        embeding_table=(pd.DataFrame(embeding_dict).T.reset_index())
    for words in (corpus):
        embeding_df=pd.concat([embeding_df,
                               embeding_table.query('@words in index').iloc[:,1:].mean()]
                             ,axis=1 )
    return embeding_df




# In[ ]:


#코사인 유사도 계산 함수
def cos_sim(A, B): 
       return dot(A, B)/(norm(A)*norm(B))


# In[45]:


#다른 모든 행과 유사도 계산 함수
def find_similar(input_name,input_prof,sim_df,detail):
    
    input_lecture = sim_df.query('name == @input_name & prof == @input_prof').iloc[:,7:]
    rest_lecture = sim_df.query('name != @input_name | prof != @input_prof').iloc[:,7:]
    
    output = sim_df.iloc[:,:7]
    output['similar']=''
    
    for i in range(len(rest_lecture)):
        output.loc[i,'similar']= cos_sim(input_lecture , rest_lecture.iloc[i,:])
    output = pd.merge(output,detail,on=['name','prof'], how = 'left')
    output = output[['name','prof','category','recommend_year','weight','학점 비율','조모임','과제','시험 횟수','출결','remarks','score','similar']]
    output = output.sort_values('similar',ascending=False)
    return output


# In[4]:


class update(object) :
    
    def __init__(self,id_,password) : 
        self.id_ = id_
        self.password = password
        self.browser = webdriver.Chrome()
    
    def login(self):
        
        self.browser.find_element_by_name('userid').send_keys(str(self.id_))
        self.browser.find_element_by_name('password').send_keys(str(self.password))
        self.browser.find_element_by_xpath('//*[@id="container"]/form/p[3]/input').click()
        
    def review_crawl(self,link_text):
        browser = self.browser
        ## Selenium
        browser.get(link_text)
        sleep(0.5) # 로딩 기다리기
        # 리뷰 내용만 추출
        reg=re.compile('[0-9]')
        reviews={}
        sleep(2) # 로딩 기다리기 
        tb=browser.find_element_by_class_name('articles')
        art_table=tb.find_elements_by_tag_name('article')

        for element in art_table :
            reviews[element.find_element_by_class_name('text').text]=(float(''.join(reg.findall(element.find_element_by_class_name('on').get_attribute('style'))))*0.05)

        # 소스 뺴와서 파싱
        table=bs(browser.page_source,'xml')
        heads=table.find('div',class_='side head')

        # 제목, 교수 내용 추출
        class_name=(heads.find('h2').text)
        prof_name=(heads.find('span').text)

        # 강의평 테이블 추출
        articles=table.find('div',class_='side article')

        # 강의평의 평균 평점 내용 추출
        mean_score=float(articles.find('span',class_='value').text)

        # 강의평 중 세부 테이블 추출
        details=articles.find('div',class_='details')

        # 강의평 중 세부 내용 추출
        labels=details.find_all('label')
        detail=details.find_all('span')
        detail_type={}
        for l,d in zip(labels,detail):
            detail_type[str(l.text)]=d.text

        review_t=pd.DataFrame.from_dict(reviews, orient='index').reset_index()
        review_t.columns=['review','score']
        review_t['name']=class_name
        review_t['prof']=prof_name

        review_detail=pd.DataFrame.from_dict(detail_type,orient='index').T
        review_detail['name']=class_name
        review_detail['prof']=prof_name


        return review_t,review_detail

        

    def lecture_update(self):
        browser = self.browser
        browser.get('https://everytime.kr/timetable')
        self.login()
        sleep(3)
        try:
            browser.find_element_by_xpath('//*[@id="sheet"]/ul/li[3]/a').click()
        except:
            sleep(3)
            browser.find_element_by_xpath('//*[@id="sheet"]/ul/li[3]/a').click()
            
        # 검색 클릭
        browser.find_element_by_xpath('//*[@id="container"]/ul/li[1]').click()
        
        # 스크롤 내리기
        scr1=browser.find_element_by_xpath('//*[@id="subjects"]/div[2]')
    
        for i in range(100):
            browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scr1)
            sleep(3)
    
        # 에타 과목 정보 저장
        tables = browser.find_elements_by_tag_name("tr")
        # 이 과목 평점 저장
        stars = browser.find_elements_by_class_name('star')
        
        # 점수랑 링크 가져오는 코드
        scores=[]
        links=[]
        for table in stars :
            scores.append(table.get_attribute('title'))
            links.append(table.get_attribute('href'))
        
        # 테이블이, 3번행부터 정보가 있고, 2918행 이후로는 의미없는 행이길래 제외 (이거 자주 바뀜 확인해줘야 할듯)
        # 테이블에서 세부정보 뽑는 코드
        tables=tables[3:3000]
        grades=[] # 추천학년
        categories=[] # 수업 분류(전공,교양)
        codes=[] # 과목코드
        names=[] # 수업 이름
        profs=[] # 교수 이름
        weights=[] # 학점(1,2,3)
        times=[] # 시간
        competitiors=[] # 에타 시간표에 담은인원
        remarks=[]
        print('과목 정보 추출')
    
        for elem in tqdm_notebook(tables):
            splited=elem.find_elements_by_tag_name('td')
            
            try:
                grades.append(splited[0].text)
                categories.append(splited[1].text)
                codes.append(splited[2].text)
                names.append(splited[3].text)
                profs.append(splited[4].text)
                weights.append(splited[5].text)
                times.append(splited[8].text)
                competitiors.append(splited[10].text)
                remarks.append(splited[11].text)
            except:
                continue
    
        # 뽑은 리스트들을 df로 바꿔줬음
        dfs=[names,codes,scores,categories,profs,times,grades,weights,competitiors,remarks,links]
        df=pd.DataFrame()
        for cols in dfs:
            df=pd.concat([df,pd.Series(cols)],axis=1)
        del tables
    
        # 칼럼 이름 만들어줌
        df.columns=['class_name','class_code','score','category','professor','time',
                'recommend_year','weight','competitor','remarks','link']
    
        # 아까 위에서 형식 제대로 안지켜진 데이터들 떨굼
        df.dropna(inplace=True)
        lecture=df.copy()
        
        file_write(lecture,'lecture')
        
   
        
    def review_embedding_update(self) :
        browser = self.browser
        review = pd.DataFrame() 
        detail = pd.DataFrame() 
        
        #링크 가져오기
        fname = input('lecture의 버전을 입력해주세요')
        lecture = pd.read_csv(str(fname))
        lecture = lecture.query('score != 0')
        link_list=list(lecture['link'].unique())
        # 링크 접근
        browser.get(link_list[0])
        sleep(1)
        
        try :
            self.login()
        except :
            print('로그인 X')
            
        try:
            sleep(5)
            browser.find_element_by_xpath('//*[@id="sheet"]/ul/li[3]/a').click()
        except:
            print('팝업없음')
            
        # 크롤링 과정
        for link in tqdm_notebook(link_list) :
            try:
                r_t,r_d=self.review_crawl(link)
                review=pd.concat([review,r_t])
                detail=pd.concat([detail,r_d])
            except:
                continue
                
                
        # 특문 없애기
        clean=[]
        for data in review['review']:
            clean.append(cleanText(data))
        review['review']=pd.Series(clean)

        file_write(review,'review')
        file_write(detail,'detail')
    
        okt = Okt()  
        corpus=[] 
    
        for data in tqdm(review['review']):
            try:
                corpus.append(okt.morphs(data))
            except:
                continue
    
        size = 100
    
        embd_SG= Word2Vec(corpus, size=size ,window=2, min_count=10,
                               workers=-1, iter=1000, sg=1)
    
        embedding_vect=get_embedding_vector(embd_SG,corpus)
        
    
        vect=(embedding_vect.T.reset_index()).iloc[:,1:] # 데이터 프레임으로 바꿔주고
        vect.columns=['Review_Embeded'+str(x) for x in range(size)] # 칼럼이름도 달아줌

        # 리뷰랑 병합(Group화 해서 강의별 계산을 위함)
        review.index=range(len(review))
        embd=pd.concat([review.iloc[:,1:],vect],axis=1)

        # 여기다 담아놓은다음에 Merge
        feature=[]
    
        for col_name in (['Review_Embeded'+str(x) for x in range(size)]):
            feature.append(embd.groupby(['name','prof'])[col_name].mean().reset_index())
        
        lecture = lecture.fillna('없음')
        lecture = lecture.drop(['class_code','time','link','competitor'],axis=1)
        lecture.rename({'class_name':'name','professor':'prof'},axis=1,inplace=True)

        
        for f in feature :
            lecture = pd.merge(lecture, f, on=['name','prof'],how='left')

        lecture.drop_duplicates(inplace=True)
        lecture.dropna(inplace=True)

        file_write(lecture,'sim_df')


