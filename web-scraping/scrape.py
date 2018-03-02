import requests
from bs4 import BeautifulSoup
import threading
import sys
import time
import pandas as pd
import re
import queue


# In[6]:

payload={'q':'Best mobiles'}


# In[9]:

try:
    r=requests.get('http://www.flipkart.com/search',params=payload)
    print("Connected to Flipkart")
except:
    print("Learn some networking ass****")


# In[46]:

soup=BeautifulSoup(r.text,'html.parser')


# In[47]:

result_temp=soup.find_all('span',attrs={'class':'_3v8VuN'})


# In[48]:

st=result_temp[0].text[-3:]
number_of_pages=int(st)
print(st)


# In[49]:

list_of_links_to_other_pages=[]


# In[50]:

list_of_links_to_other_pages.append('https://www.flipkart.com/search?q=best%20mobiles&otracker=start&as-show=on&as=off')
for i in range (2,number_of_pages+1):
    string_temp='https://www.flipkart.com/search?as=off&as-show=on&otracker=start&page={}&q=best+mobiles&viewType=list'.format(i)
    list_of_links_to_other_pages.append(string_temp)


# In[51]:

global_comment_dic={}
final_list_of_dic_of_phone=queue.Queue(0)
queue_of_links=queue.Queue(0)

listlock1=threading.RLock()


# In[52]:

def extract_phones_on_ith_page(link,pgno):
   # print(link+" "+str(pgno))
    mydata=threading.local()
    try:
        r=requests.get(link)
    except:
        print("extract_phones_on_page{} hagdiya".format(pgno))
        return
    soup1=BeautifulSoup(r.text,'html.parser')
    phones_on_cur_page=soup1.find_all('a',attrs={'class':'_1UoZlX'})
    name=soup1.find_all('div',attrs={'class':'_3wU53n'})
    cost=soup1.find_all('div',attrs={'class':'_1vC4OE _2rQ-NK'})
    #print(str(pgno)+" "+str(len(phones_on_cur_page)))
    temp_namer=[]
    temp_coster=[]
    temp_link=[]
    #print("len of name "+str(len(name))+" "+"len of cost "+str(len(cost))+" "+link)
    #print(len(name)==len(phones_on_cur_page))
    for i in range(0,len(phones_on_cur_page)):
        link1="https://www.flipkart.com"+phones_on_cur_page[i]['href']
        if link1 not in temp_link:
            temp_link.append(link1)
            #temp_coster.append(cost[i].text)
            #temp_namer.append(name[i].text)
    try:
        listlock1.acquire()
        for i in range(0,len(temp_link)):
            queue_of_links.put(temp_link[i])
    finally:
        listlock1.release()


# In[53]:

start=time.time()
thread_list=[]
for i in range(0,82):
    try:
        t=threading.Thread(target=extract_phones_on_ith_page,name='thread_for_{}page'.format(i),args=(list_of_links_to_other_pages[i],i))
        thread_list.append(t)
        t.start()
    except:
        print("Threading not working while looping. Par Kyon?")
for i in thread_list:
    i.join()
end=time.time()
print(end-start)
print("count "+str(threading.active_count()))


# In[54]:

list_of_links=[]


# In[55]:

cnt=0
while True:
    if queue_of_links.empty()==True:
        break
    gg=queue_of_links.get()
    list_of_links.append(gg)
    cnt+=1
print(cnt)


# In[56]:

templen=set(list_of_links)


# In[57]:

print(len(templen))
print(len(list_of_links))


# In[58]:

final_list_of_dic_of_phone=queue.Queue(0)
link_for_review=[]
cnt1=0
cnt2=0
cntg=0


# In[59]:

def get_phone_features(link,phno):
    #print(link+" "+str(phno))
    mydata=threading.local()
    try:
        r=requests.get(link)
    except:
        print("get phone feature from {} haga".format(phno))
        print(link)
        thread.exit()
    dic={}#This dictionary stores all the features of the phone
    soup1=BeautifulSoup(r.text,'html.parser')
    name_of_feature=soup1.find_all('div',attrs={'class':'vmXPri col col-3-12'})
    #<div class="_3wU53n">Redmi Note 4 (Black, 64 GB)</div>
    actual_feature=soup1.find_all('li',attrs={'class':'sNqDog'})
    namer=soup1.find_all('h1',attrs={'class':'_3eAQiD'})
    coster=soup1.find_all('div',attrs={'class':'_1vC4OE _37U4_g'})
    imgsrc=soup1.find_all('img',attrs={'class':'sfescn'})
    imglink=""
    if len(imgsrc)!=0:
        imglink=imgsrc[0]['src']
    print(imglink)
    if len(namer)==0 or len(coster)==0:
        return
    try:
        dic['Name']=namer[0].text
    except:
        cnt1+=1
       # print("Na mila naam, na mila paisa")
        return
    try:
        dic['Cost']=coster[0].text
        dic['Imgsrc']=imglink
    except:
        cnt2+=1
        return
    if len(name_of_feature)==len(actual_feature):
        for i in range(0,len(name_of_feature)):
            key=name_of_feature[i].text
            dic[key]=actual_feature[i].text
    #print(str(len(dic))+"  len of dic"+nameg+" "+costg)
    #<h1 class="_3eAQiD
    link_temp=soup1.find_all('a',attrs={'href':re.compile(r"product-reviews")})
    if len(link_temp)!=0:
        dic['reviewlink']="https://www.flipkart.com"+link_temp[0]['href']
    else:
        cntg+=1
    try:
        listlock1.acquire()
        final_list_of_dic_of_phone.put(dic)
    finally:
        listlock1.release()
    
    #get_reviews(link_for_reviews,dic['Name'])
    #Final list is a list of dictionary that would be converted to pandas dataframe


# In[60]:

start=time.time()
thread_list=[]
for i in range(len(list_of_links)):
    t=threading.Thread(target=get_phone_features,name='thread_for_{}page'.format(i),args=(list_of_links[i],i))
    thread_list.append(t)
    t.start()
    #print("Multithreading sucks")
for i in thread_list:
    i.join()
end=time.time()
print(end-start)


# In[61]:

print(final_list_of_dic_of_phone.qsize())
lis_of_dic=[]
while final_list_of_dic_of_phone.empty()!=True:
    ele=final_list_of_dic_of_phone.get()
    lis_of_dic.append(ele)
print(len(lis_of_dic))


# In[62]:

pp=set()
liname=[]
for i in lis_of_dic:
    liname.append(i['Name'])
    pp.add(i['Name'])
liname=sorted(liname)
for i in liname:
    print(i)


# In[63]:

print(len(pp))
lis_of_comment_link=[]
global_comment_dic={} #name and comment pair


# In[28]:

lis_of_dicf=[]
for i in pp:
    lis_of_dicf.append(i)


# In[110]:

def get_reviews(name,link):
    #print(link+" "+name)
    r1=requests.get(link)
    soup1=BeautifulSoup(r1.text,'html.parser')
    number_of_review_pages=soup1.find_all('div',attrs={'class':'_1JKxvj _1vKM3Y'})
    #<span class="_3v8VuN"><span><!-- react-text: 2537 -->Page 1 of 1,263<!-- /react-text --></span></span>
    #<div class="_1JKxvj _1vKM3Y"><span class="_3v8VuN"><span><!-- react-text: 2537 -->Page 1 of 1,263<!-- /react-text --></span></span><ul class="_316MJb"><li class="_1mO8v9"><a class="_33m_Yg _2udQ2X" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=1&amp;pid=MOBFF5ZG7HCKHJCS">1</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=2&amp;pid=MOBFF5ZG7HCKHJCS">2</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=3&amp;pid=MOBFF5ZG7HCKHJCS">3</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=4&amp;pid=MOBFF5ZG7HCKHJCS">4</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=5&amp;pid=MOBFF5ZG7HCKHJCS">5</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=6&amp;pid=MOBFF5ZG7HCKHJCS">6</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=7&amp;pid=MOBFF5ZG7HCKHJCS">7</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=8&amp;pid=MOBFF5ZG7HCKHJCS">8</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=9&amp;pid=MOBFF5ZG7HCKHJCS">9</a></li><li class="_1mO8v9"><a class="_33m_Yg" href="/honor-9-lite-midnight-black-32-gb/product-reviews/itmff5zgdeckztpk?page=10&amp;pid=MOBFF5ZG7HCKHJCS">10</a></li></ul><div class="_2kUstJ"><a href="/honor-9-li
   
    list_of_page_links=[]
    first_page=soup1.find('a',attrs={'class':'_33m_Yg _2udQ2X'})
    print(first_page)
    '''link_of_other_pages=soup1.find_all('a',attrs={'class':'_33m_Yg'})
    if len(first_page)!=0:
        list_of_page_link.append(first_page[0]['href'])
    else:
        print("GG first page par Haga.Agey kaisey jayega chutiye")
    for i in link_of_other_pages:
        list_of_page_links.append("www.flipkart.com/"+i[0]['href'])
    for i in range(min(10,len(list_of_page_links))):
        try:
            t=threading.Thread(target=get_comments_from_page,name='thread@{}'.format(i),args=(list_of_page_links[i],name))
            t.start()
        except:
            print("Learn some threading noobu,get reviews rekt")
            return'''


# In[96]:

def get_comments_from_page(link,name):
    try:
        r=requests.get(link)
    except:
        return
    soup1=BeautifulSoup(r.text,'html.parser')
    title_list=soup1.find_all('p',attrs={'class':'_2xg6Ul'})
    comment_list=soup1.find_all('div',attrs={'class':'qwjRop'})
    stars=soup1.find_all('div',attrs={'class':'hGSR34 _2beYZw E_uFuv'})
    title_list_text=[]
    stars_text=[]
    comment_list_text=[]
    for i in title_list:
        title_list_text.append(i.text)
    for i in stars:
        stars_text.append(i.stars)
    for i in comment_list:
        comment_list_text.append(i.text)
    if(len(title_list)==len(comment_list)):
        global_comment_dic[name]=(title_list_text,comment_list_text,stars_text)
    else:
        return 


# In[93]:

df=pd.DataFrame(lis_of_dicf)
df.to_csv('phones.csv')


# In[65]:

final_lis=[]
for i in lis_of_dic:
    if i in final_lis:
        continue
    else:
        lis_of_comment_link.append((i['Name'],i['reviewlink']))
        final_lis.append(i)



# In[66]:

len(final_lis)


# In[72]:

df=pd.DataFrame(final_lis)
df.to_csv('phonesfeaturesgg.csv')


# In[73]:

dfcheck=pd.read_csv('phonesfeaturesgg.csv')


# In[74]:

print(dfcheck.head())


# In[71]:

dfhagra=pd.DataFrame(final_lis)


# In[69]:

cnt=0
key="Browse Type"
for i in final_lis:
    if key in i:
        if i[key]=="Smartphones":
            cnt+=1
        else:
            print(i['Name']+i[key])
    else:
        print(i['Name'])
print(cnt)


# In[70]:

dfhagra.to_csv('f22.csv')


# In[ ]:

def get_reviews(link,name):
    try:
        r=requests.get(link)
    except:
        print("Get reviews haga")
        return
    soup1=BeautifulSoup(r.text,'html.parser')
    number_of_review_pages=soup1.find_all('span',attrs={'class':'_3v8VuN'})
    if len(number_of_review_pages)!=0:
        str_pages=number_of_review_pages[0].text[-4:]
        if(str_pages[0]<='9'):
            pages=int(str_pages)
        elif(str_pages[1]<='9'):
            pages=int(str_pages[1:])
        elif(str_pages[2]<='9'):
            pages=int(str_pages[2:])
        elif(str_pages[3]<='9'):
            pages=int(str_pages[3:])
        else:
            pages=0
            return
    else:
        print("Good game bro.No pages found dude")
        return
    list_of_page_links=[]
    first_page=soup1.find('a',attrs={'class':'_33m_Yg _2udQ2X'})
    link_of_other_pages=soup1.find_all('a',attrs={'class':'_33m_Yg'})
    if(len(first_page)!=0):
        list_of_page_link.append(first_page[0]['href'])
    else:
        print("GG first page par Haga.Agey kaisey jayega bro")
    for i in link_of_other_pages:
        list_of_page_links.append("www.flipkart.com/"+i[0]['href'])
    for i in range(0,min(1,len(list_of_page_links))):
        try:
            t=threading.Thread(target=get_comments_from_page,name='thread@{}'.format(i),args=(list_of_page_links[i],name))
            t.start()
        except:
            print("Learn some threading noobie, get reviews rekt")
            return