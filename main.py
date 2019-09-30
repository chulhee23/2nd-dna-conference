#!/usr/bin/env python
# coding: utf-8

# In[3]:


# 파일 생성 함수
def file_write(df,name):
    
    t = pd.Timestamp.now()
    fname = str(name) + str(t.month) + str(t.day) + ".csv"
    
    print(str(name) + '파일 생성 | 이름 : ' + str(fname))

    df.to_csv(fname,index=False)


# In[15]:


# login 함수 생성
def login(id_,password):
    browser.find_element_by_name('userid').send_keys(str(id_))
    browser.find_element_by_name('password').send_keys(str(password))
    browser.find_element_by_xpath('//*[@id="container"]/form/p[3]/input').click()


# In[16]:


# 특수문자 제거
def cleanText(readData):
    text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', ' ', readData) # 특문제거
    return text


# In[17]:


def lecture_update(id_,password):
    
    # Browser 켜기
    browser = webdriver.Chrome()
    browser.get('https://everytime.kr/timetable')
    
    # login
    login(id_,password)
    sleep(3)
        
    # 가끔 팝업뜨는거 닫아주기
    try:
        browser.find_element_by_xpath('//*[@id="sheet"]/ul/li[3]/a').click()
    except:
        print('팝업 안닫혔음, 확인부탁')
    
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
    
    file_write(lecture,lecture)


    #return df2

    


# In[3]:


def review_crawl(link_text):
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

    
    #return review_t,review_detail


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


# In[1]:


def review_embedding_update():
    review = pd.DataFrame() # 강의평 추출 테이블
    detail = pd.DataFrame() # 과목 세부정보 추출 테이블

    
    #링크 가져오기
    fname = input('lecture의 버전을 입력해주세요')
    lecture = pd.read_csv(str(fname))
    lecture = lecture.query('score != 0')
    link_list=list(lecture['link'].unique())
    link_list.remove('javascript: alert("%EC%95%84%EC%A7%81 %EB%93%B1%EB%A1%9D%EB%90%9C %EA%B0%95%EC%9D%98%ED%8F%89%EC%9D%B4 %EC%97%86%EC%8A%B5%EB%8B%88%EB%8B%A4.");')

    
    # ↓ 가끔 안 켜고 시작하면 오류뜰 때가 있어서 그때 대비 
    browser = webdriver.Chrome()
    browser.get(link_list[0]) 
    login(id_,password)
    # ↑ 가끔 안 켜고 시작하면 오류뜰 때가 있어서 그때 대비 


    # 크롤링 과정
    for link in tqdm_notebook(link_list) :
        try:
            r_t,r_d=review_crawl(link)
            review=pd.concat([review,r_t])
            detail=pd.concat([detail,r_d])
            sleep(1)
        except:
            continue

    # 특문 없애기
    clean=[]
    for data in review['review']:
        clean.append(cleanText(data))
    review['review']=pd.Series(clean)

    file_write(review,review)
    file_write(detail,detail)
    
    kkma = Kkma()  
    corpus=[] 
    
    for data in tqdm(review['review']):
        try:
            corpus.append(kkma.morphs(data))
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
        
    lecture = lecture.drop(['class_code','time','link','competitor'],axis=1)
    lecture.rename({'class_name':'name','professor':'prof'},axis=1,inplace=True)

    for f in feature :
        df = pd.merge(lecture, f, on=['name','prof'],how='left')

    df.drop_duplicates(inplace=True)
    df.dropna(inplace=True)

    sim_df=pd.concat([df[['name','prof',]],df.iloc[:,7:]],axis=1)
    sim_df.index=[x for x in range(len(sim_df))]
    file_write(sim_df,sim_df)


# In[ ]:


#코사인 유사도 계산 함수
def cos_sim(A, B): 
       return dot(A, B)/(norm(A)*norm(B))


# In[45]:


#다른 모든 행과 유사도 계산 함수
def find_similar(input_name,input_prof,df):
    input_lecture=df.query('name == @input_name & prof == @input_prof')
    rest_lecture=df.query('name != @input_name | prof != @input_prof')
    output=rest_lecture.iloc[:,:2]
    output['similar']=''
    for i in range(len(rest_lecture)):
        output.iloc[i,2]= cos_sim(input_lecture.iloc[:,2:],rest_lecture.iloc[i,2:])
    output = pd.merge(output, detail_table, on=['name','prof'],how='left')
    output = output.sort_values('similar',ascending=False)
    return output


# In[5]:


def update_all():
    lecture_update()
    review_embedding_update()


# In[4]:


def ready_data_all():
    os.listdir()
    ver=input('버전을 입력하세요')
    lecture=pd.read_csv('lecture'+str(ver)+'.csv')
    review=pd.read_csv('review'+str(ver)+'.csv')
    detail=pd.read_csv('detail'+str(ver)+'.csv')
    sim_df=pd.read_csv('sim_df'+str(ver)+'.csv')

