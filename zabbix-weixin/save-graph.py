#!/usr/bin/python
#coding=utf-8
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import smtplib,sys,os,time,re

user='***'
#zabbix用户名
password='****'
#zabbix密码
url='http://xx.xx.xx.xx[:xx]/zabbix/index.php'
#zabbix首页
period='3600'
#时间周期 1 小时
chart2_url='xx.xx.xx.xx[:xx]/zabbix/chart2.php?width=1084'
chart6_url='xx.xx.xx.xx[:xx]/zabbix/chart6.php?width=1084'
#zabbix获取图片,chart2 折线图，chart6 饼图

graph_path='/data/graph/'
#图片保存路径

graphids=('736','747','739','758')
graphidurls=('2','2','2','6')

def get_graph():
    #拉取图片
    time_tag=time.strftime("%Y%m%d%H%M%S", time.localtime())
    graph_name = []
    os.system('curl -L -c /tmp/cookie.txt --user-agent Mozilla/4.0  -d "reauest=&name=%s&password=%s&autologin=1&enter=Sign+in"  %s' %(user,password,url))
    for i in range(len(graphids)):
        if graphidurls[i] == '2':
            os.system('curl -c /tmp/cookie.txt -b /tmp/cookie.txt --user-agent Mozilla/4.0 -F "graphid=%s" -F "period=%s" -F "width=900" %s > %s/zabbix_%s_%s.png' %(graphids[i],period,chart2_url,graph_path,graphids[i],time_tag))
        else:
            os.system('curl -c /tmp/cookie.txt -b /tmp/cookie.txt --user-agent Mozilla/4.0 -F "graphid=%s" -F "period=%s" -F "width=900" %s > %s/zabbix_%s_%s.png' %(graphids[i],period,chart6_url,graph_path,graphids[i],time_tag))
        graph_name.append('/data/graph/' + 'zabbix_' + graphids[i] + '_' + time_tag  +'.png')
    return graph_name

def send_mail(to_email,subject):
     #发送邮件
     graph_names=get_graph()
     html_text=''
     smtp_host = 'smtphm.qiye.163.com'
     from_email = 'xx@xxx.com'
     #邮箱账户
     passwd = 'xx'
     #邮箱密码
     msg=MIMEMultipart('related')
     html="""
      <html>
       <body>
    <table>
     """
     for graph_name in graph_names:
         fp=open(graph_name,'rb')
         image=MIMEImage(fp.read())
         fp.close()
         image.add_header('Content-ID',"%s" %graph_name)
         msg.attach(image)

         html+=html_text
         html+="<tr><td><img src='cid:%s'></td></tr>" %graph_name
         html+="<tr><td><hr /></td></tr>"
     html+="""
       </table>
        </body>
         </html>
     """
     html=MIMEText(html,'html','utf-8')
     msg.attach(html)
     msg['Subject'] = subject
     msg['From'] = from_email
     msg['to'] = ",".join(list_to)
     smtp_server=smtplib.SMTP_SSL()
     smtp_server.connect(smtp_host,'465')
     smtp_server.login(from_email,passwd)
     smtp_server.sendmail(from_email,to_email,msg.as_string())
     smtp_server.quit()
     
if __name__ == '__main__':
  subject='Server performance report'
  list_to = [
                "xx1@xx.com", "xx2@xx.com", "xx3@xx.com"
            ]
  send_mail(list_to,subject)

