from django.shortcuts import render,redirect
from .forms import RegistrationForm,codeForm,AssignmentForm,updatePass,feedbackForm,WorkForm,CourseForm,ChatSearchForm,OTP,OTP_update
from .mail import assign_notif,announce_notif,submit_notif,eval_notif,otp_notice
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from .models import Chat, Person,Work,Assignment,Course,Announcements
from django.core.files.storage import FileSystemStorage
from datetime import datetime
import pytz
import random
from .drive import uploadFile

utc=pytz.UTC

def home(request):
    return render(request,'main_home.html')

def register(request):
    if(request.method=='POST'):
        form=RegistrationForm(request.POST)
        if form.is_valid():
            x = form.save()
            if (not(Person.objects.filter(user = x).exists())):
                    a = Person(user = x)
                    a.save()
            return redirect('/login/')
        else:
            form=RegistrationForm()
            return render(request,'signup.html',{'form':form})
    else:
        form=RegistrationForm()
        return render(request,'signup.html',{'form':form})

def Login(request):
    if(request.method=='POST'):
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            uname=form.cleaned_data['username']
            upass=form.cleaned_data['password']
            user = authenticate(username=uname, password=upass)
            if user is not None:
                login(request, user)
                if (not(Person.objects.filter(user = request.user).exists())):
                    a = Person(user = request.user)
                    a.save()
                #current = Person.objects.get(user = request.user)
                #works = []
                #for w in Work.objects.all():
                #    if w.owner == current.user.username:
                #        works.append(w)
                #all_works = Work.objects.all()
                return redirect('course_page/')
                #return render(request,'course_page.html',{'all_works':all_works, 'works':works})
                #return render(request,'course_page.html',{'Person':request.user})
        else:
            return redirect('login/')
    else:
        form=AuthenticationForm()
        return render(request,'login.html',{'form':form})


def course(request):
    if request.user.is_authenticated:
        if (not(Person.objects.filter(user = request.user).exists())):
                    a = Person(user = request.user)
                    a.save()
        current = Person.objects.get(user = request.user)
        if (request.method == 'POST'):
            form = codeForm(request.POST)
            if form.is_valid():
                code = form.cleaned_data['Code']
                instance = code.split('.')
                if(current in Course.objects.get(name = instance[0]).students.all()):
                    path = '/course_page/'+instance[0]+'/'+instance[1]+'/'
                    return redirect(path)
                else:
                    path = '/course_page/'
                    return redirect(path)
            else:
                form = codeForm()
        else:
            form = codeForm()

        courses_under = []
        courses_enrolled = []
        prcnt = {}
        for c in Course.objects.all():
            if c.educator.user.username == current.user.username:
                courses_under.append(c)
            elif current in c.ta.all():
                courses_under.append(c)
            elif current in c.students.all():
                courses_enrolled.append(c)
                i = 0
                for w in c.work_set.all():
                    for a in w.assignment_set.all():
                        if(a.name == current.user.username):
                           i = i+1
                if(c.work_set.all().count()!=0):
                    prcnt[c.name] = str((i*100)/(c.work_set.all().count()))
                else:
                    prcnt[c.name] = str(100.0)
                print(prcnt)
            print(courses_enrolled)
        return render(request,'course_page.html',{'form':form, 'courses':courses_under, 'prcnt':prcnt}) #prcnt
    else:
        return redirect('login/')

def todo(request):
    current = Person.objects.get(user = request.user)
    eval = []
    attempt = []
    for c in Course.objects.all():
      if c.educator.user.username == current.user.username:
        if(Work.objects.all().count() != 0):
            for w in Work.objects.all():
                if w.crs.name == c.name:
                    for a in w.assignment_set.all():
                        if(a.obtained_marks == -1):
                            eval.append(w)
                            break 
      elif current in c.ta.all():
        if(Work.objects.all().count() != 0):
            for w in Work.objects.all():
                if w.crs.name == c.name:
                    for a in w.assignment_set.all():
                        if(a.obtained_marks == -1):
                            eval.append(w)
                            break 
      elif current in c.students.all():
        if(Work.objects.all().count() != 0):
            for w in c.work_set.all():
                if(w.deadline):
                    if(w.deadline < utc.localize(datetime.now()) ):
                        continue
                found = False
                for a in w.assignment_set.all():
                   if(a.name == current.user.username):
                       found = True
                       break
                if(found == False):
                    attempt.append(w)
    args = {'Person':current, 'eval':eval, 'attempt':attempt}
    return render(request,'todo.html',args)

def chats(request):
    active_chats = []
    for c in Chat.objects.all():
        if (c.end1.user.username == request.user.username):
            active_chats.append(c.end2.user.username)
        elif (c.end2.user.username == request.user.username):
            active_chats.append(c.end1.user.username)      
    if(request.method=="POST"):
        form=ChatSearchForm(request.POST)
        if form.is_valid():
            for c in Chat.objects.all():
                if ((c.end1.user.username == request.user.username and c.end2.user.username == form.cleaned_data['name']) or (c.end2.user.username == request.user.username and c.end1.user.username == form.cleaned_data['name'])):
                    path='/course_page/chats/'+form.cleaned_data['name']+'/'
                    return redirect(path)
            end_2 = Person.objects.get(user = request.user)
            for p in Person.objects.all():
                if p.user.username == form.cleaned_data['name']:
                    end_2 = p
            c = Chat(end1 = Person.objects.get(user = request.user), end2 = end_2)
            c.save()
            path = '/course_page/chats/'+form.cleaned_data['name']+'/'
            return redirect(path)
        else:
            form=ChatSearchForm()
            args={'form':form, 'active_chats':active_chats}
            return render(request,'chat_active.html',args)
    else:
        form=ChatSearchForm()
        args={'form':form, 'active_chats':active_chats}
        return render(request,'chat_active.html',args)

def dm(request, item):
    current = Person.objects.get(user = request.user)
    for c in Chat.objects.all():
        if ((c.end1.user.username == current.user.username and c.end2.user.username == item) or (c.end2.user.username == current.user.username and c.end1.user.username == item)):
            if(request.method=="POST"):
                if request.POST.get("chkvalue"):
                    temp = c.content+'\n'+current.user.username+': '+request.POST.get("chkvalue")
                    c.content = temp
                    c.save()
                    print(c.content)
                path = '/course_page/chats/'+item+'/'
                return redirect(path)        
            else:
                print(c.content)
                txt = c.content.split('\n')
                txt = txt[1:]
                return render(request,'dm.html',{'txt':txt, 'name':item})    
            


def create_course(request):
    if(request.method=="POST"):
        form=CourseForm(request.POST)
        if form.is_valid():
            ed = Person.objects.get(user = request.user)
            cs = Course(educator=ed,name=form.cleaned_data['name'],mem_ta_allowed=form.cleaned_data['Member_allowance_to_TA'],create_ta_allowed=form.cleaned_data['Creation_allowance_to_TA'])
            cs.save()
            args={'cs':cs}
            return render(request,'create_course.html',args)
        else:
            form=CourseForm()
            args={'form':form}
            return render(request,'c_course.html',args)
    else:
        form=CourseForm()
        args={'form':form}
        return render(request,'c_course.html',args)

def enter_course(request, item):
    current = Person.objects.get(user = request.user)
    c = Course.objects.get(name = item)
    if (request.method == 'POST'):
        form = codeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['Code']
            instance = code.split('.')
            if(current in c.students.all()):
                path = '/course_page/'+instance[0]+'/'+instance[1]+'/'
                return redirect(path)
            else:
                path = '/course_page/'+instance[0]+'/'
                return redirect(path) 
        else:
            form = codeForm()
    else:
        form = codeForm()
    flag = 0
    works = []
    announce = c.announcements_set.all()
    if c.educator.user.username == current.user.username:
        flag = 0
        if(Work.objects.all().count() != 0):
            for w in Work.objects.all():
                if w.crs.name == c.name:
                    for a in w.assignment_set.all():
                        if(a.obtained_marks == -1):
                            works.append(w)
                            break 
        args = {'c':c, 'Person':current, 'works':works, 'form':form, 'announce':announce}
        return render(request,'ed_look.html',args)
    elif current in c.ta.all():
        flag = 1
        if(Work.objects.all().count() != 0):
            for w in Work.objects.all():
                if w.crs.name == c.name:
                    for a in w.assignment_set.all():
                        if(a.obtained_marks == -1):
                            works.append(w)
                            break 
        args = {'c':c, 'Person':current, 'works':works, 'form':form, 'announce':announce}
        return render(request,'ta_look.html',args)
    else :
        flag = 2
        if(Work.objects.all().count() != 0):
            for w in Work.objects.all():
                if w.crs.name == c.name:
                    works.append(w)
        args = {'c':c, 'Person':current, 'works':works, 'form':form, 'announce':announce}
        return render(request,'stud_look.html',args)

def course_chat(request, item):
    current = Person.objects.get(user = request.user)
    c = Course.objects.get(name = item)
    ed_bool = False
    if(c.educator.user.username == current.user.username):
        ed_bool = True
    if(request.method=="POST"):
            if request.POST.get("chkvalue"):
                if(ed_bool == True and request.POST.get("chkvalue")=='DISABLE'):
                    c.chat_allowed = False
                if(ed_bool == True and request.POST.get("chkvalue")=='ENABLE'):
                    c.chat_allowed = True
                temp = c.chat_content+'\n'+current.user.username+': '+request.POST.get("chkvalue")
                c.chat_content = temp
                c.save() 
            path = '/course_page/'+item+'/course_chat/'
            return redirect(path)        
    else:
        txt = c.chat_content.split('\n')
        txt = txt[1:]
        return render(request,'course_forum.html',{'ed_bool':ed_bool, 'txt':txt, 'name':item, 'allowed':c.chat_allowed})    


def announce(request, item):
    c = Course.objects.get(name = item)
    if(request.method=="POST"):
        if request.POST.get("chkvalue"):
            a = Announcements(crs=c, content=request.POST.get("chkvalue"))
            a.save()
            announce_notif(c.educator.user.username,c.educator.user.email,item,request.POST.get("chkvalue"))
            for i in c.ta.all():
                announce_notif(i.user.username,i.user.email,item,request.POST.get("chkvalue"))
            for i in c.students.all():
                announce_notif(i.user.username,i.user.email,item,request.POST.get("chkvalue"))
            path = '/course_page/'+item+'/'
            return redirect(path)         
    else:
        return render(request,'announce.html')    


def members(request, item):
    current = Person.objects.get(user = request.user)
    c = Course.objects.get(name = item)
    tas = c.ta.all()
    studs = c.students.all()
    return render(request,'mem.html',{'tas':tas, 'studs':studs, 'current':current, 'c':c})

def add_ta(request, item):
    c = Course.objects.get(name = item)        
    people = []
    for p in Person.objects.all():
        if ((p.user.username != c.educator.user.username)  and  (p not in c.ta.all())  and  (p not in c.students.all())):
            people.append(p)
    if(request.method=="POST"):
        if request.POST.get("chkvalue"):
            for p in people:
                if p.user.username == request.POST.get("chkvalue"):
                    c.ta.add(p)
                    break
        path = '/course_page/'+item+'/members/'
        return redirect(path)        
    else:
        return render(request,'add_ta.html',{'people':people})    

def remove_ta(request, item):
    c = Course.objects.get(name = item)
    people = []
    for p in Person.objects.all():
        if p in c.ta.all():
            people.append(p)
    if(request.method=="POST"):
        if request.POST.get("chkvalue"):
            for p in people:
                if p.user.username == request.POST.get("chkvalue"):
                    c.ta.remove(p)
                    break
        path = '/course_page/'+item+'/members/'
        return redirect(path)         
    else:
        return render(request,'remove_ta.html',{'people':people})  

def add_stud(request, item):
    c = Course.objects.get(name = item)
    people = []
    for p in Person.objects.all():
        if ((p.user.username != c.educator.user.username)  and  (p not in c.ta.all())  and  (p not in c.students.all())):
            people.append(p)
    if(request.method=="POST"):
        if request.POST.get("chkvalue"):
            for p in people:
                if p.user.username == request.POST.get("chkvalue"):
                    c.students.add(p)
                    break
        path = '/course_page/'+item+'/members/'
        return redirect(path)         
    else:
        return render(request,'add_stud.html',{'people':people}) 

def remove_stud(request, item):
    c = Course.objects.get(name = item)
    people = []
    for p in Person.objects.all():
        if p in c.students.all():
            people.append(p)
    if(request.method=="POST"):
        if request.POST.get("chkvalue"):
            for p in people:
                if p.user.username == request.POST.get("chkvalue"):
                    c.students.remove(p)
                    break
        path = '/course_page/'+item+'/members/'
        return redirect(path)         
    else:
        return render(request,'remove_stud.html',{'people':people})  

def Logout(request):
    if request.user.is_authenticated:
        logout(request)
        return render(request,'main_home.html')
    else :
        return render(request,'main_home.html')

def create(request, item): 
    if(request.method=="POST"):
        form=WorkForm(request.POST)
        if form.is_valid():
            c = Course.objects.get(name = item)
            ass=Work(crs=c,name=form.cleaned_data['name'],total_marks=form.cleaned_data['total_marks'],deadline=form.cleaned_data['deadline'])
            ass.save()
            code = ass.crs.name + '.' + ass.name
            assign_notif(c.educator.user.username,c.educator.user.email,code,0)
            for i in c.ta.all():
                assign_notif(i.user.username,i.user.email,code,1)
            for i in c.students.all():
                assign_notif(i.user.username,i.user.email,code,2)
            args={'c':c,'name':ass.name,'tot':ass.total_marks,'deadline':ass.deadline}
            return render(request,'create_work.html',args)
        else:
            form=WorkForm()
            args={'form':form}
            return render(request,'c_work.html',args)
    else:
        form=WorkForm()
        args={'form':form}
        return render(request,'c_work.html',args)

def select_work(request, item):
    if(request.user.is_authenticated):
        current = Person.objects.get(user = request.user)
        c = Course.objects.get(name = item)
        works = c.work_set.all()
        return render(request,'select_work_page.html',{'works':works})
    else:
        form=AuthenticationForm()
        return render(request,'login.html',{'form':form})

def evaluate(request, item, wrk):
    if(request.user.is_authenticated):
        current = Person.objects.get(user = request.user)
        work_obj = Work.objects.get(name = wrk)
        assignments = work_obj.assignment_set.all()
        '''for a in Assignment.objects.all():
            if a.work == work_obj:
                assignments.append(a)'''
        return render(request,'evaluate.html',{'assignments':assignments, 'name':wrk})
    else:
        form=AuthenticationForm()
        return render(request,'login.html',{'form':form})
    
def user_update(old_name,new_name):
    for i in Work.objects.all():
        if i.owner==old_name:
            i.owner=new_name
            i.save()
    for i in Assignment.objects.all():
        if i.name==old_name:
            i.name=new_name
            i.save()
otp_obj=None
def secure_update(request,*args,**kwargs):
    global otp_obj
    if request.user.is_authenticated:
        if(request.method=='POST'):
            if(otp_obj!=None):
                form=OTP(request.POST)
                if form.is_valid():
                    if otp_obj.check(form.cleaned_data['otp_enter'])==-1:
                        return redirect('/course_page/')
                    elif otp_obj.check(form.cleaned_data['otp_enter'])==0:
                        otp_obj=None
                        return redirect('/course_page/')
                    elif otp_obj.check(form.cleaned_data['otp_enter'])==1:
                        form_m=updatePass({'username':request.user.username,'first_name':request.user.first_name,'last_name':request.user.last_name,'email':request.user.email})
                        otp_obj=None
                        return render(request,'update.html',{'current':request.user, 'form':form_m})
                else:
                    form=OTP()
                    return render(request,'otp.html',{'form':form})
            else:
                return redirect('/course_page/')
        else:
            otp_obj=OTP_update(random.randint(1111,9999))
            otp_notice(request.user.username,request.user.email,otp_obj.otp_real)
            form=OTP()
            return render(request,'otp.html',{'form':form})
    else:
        form=AuthenticationForm()
        return render(request,'login.html',{'form':form})
            
def grade_csv(request,course_name,work_name,file_path):
    pass

def update(request,*args,**kwargs):
    if request.user.is_authenticated:
        if(request.method=='POST'):
            form=updatePass(request.POST)
            if form.is_valid():
                user=authenticate(username=request.user.username,password=form.cleaned_data['old_password'])
                if user is not None:
                    user_update(request.user.username,form.cleaned_data['username'])
                    user.username=form.cleaned_data['username']
                    user.email=form.cleaned_data['email']
                    user.first_name=form.cleaned_data['first_name']
                    user.last_name=form.cleaned_data['last_name']
                    if form.data['password']:
                        user.set_password(form.cleaned_data['password'])
                        user.save()
                    user.save()
                return redirect('/course_page/')
            else:
                form=updatePass({'username':request.user.username,'first_name':request.user.first_name,'last_name':request.user.last_name,'email':request.user.email})
        else:
            form=updatePass({'username':request.user.username,'first_name':request.user.first_name,'last_name':request.user.last_name,'email':request.user.email})
        return render(request,'update.html',{'current':request.user, 'form':form})
    else:
        form=AuthenticationForm()
        return render(request,'login.html',{'form':form})
    



def submit(request, item, wrk):
    if (request.method == 'POST'): 
        print('yes')
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            ass = form.save(commit=False)
            for w in Work.objects.all():
                if w.name == wrk:
                    ass.name = request.user.username
                    ass.work = w
                    ass.obtained_marks = -1
                    ass.save()
                    submit_notif(request.user.username,request.user.email,wrk,w.crs.name)
                    status = False
                    uploadFile(str(ass.path) + str(w.name)) # Swayam
                    return render(request, 'show.html',{'assign':ass, 'status':status})
        else:
            form = AssignmentForm()
    else:
        if request.user.is_authenticated:
            current = Person.objects.get(user = request.user)
        try:
            work_obj = Work.objects.get(name = wrk)
        except:
            work_obj=None
        for a in work_obj.assignment_set.all():
            if (a.name == request.user.username):
                status = True
                if(a.obtained_marks == -1):
                    status = False
                return render(request, 'show.html',{'assign':a, 'status':status})
        form = AssignmentForm()
        dead = False
        if(work_obj.deadline):
            dead = work_obj.deadline < utc.localize(datetime.now()) 
        return render(request, 'submit.html', {'form':form, 'work':work_obj, 'dead_bool':dead})

def feedback(request, item, wrk, asn):
    if (request.method == 'POST'):
        form = feedbackForm(request.POST)        
        work_obj = Work.objects.get(name = wrk)
        for a in Assignment.objects.all():
            if (a.work == work_obj and a.name == asn):
                if form.is_valid():
                    a.obtained_marks = form.cleaned_data['Marks_Obtained']
                    a.save()
                    eval_notif(request.user.username,request.user.email,wrk,work_obj.crs.name)
                    status = True
                    return render(request, 'give_feedback.html',{'assign':a, 'status':status})
                else:
                    form = feedbackForm()
                    status = False
                    return render(request, 'give_feedback.html',{'assign':a, 'status':status, 'form':form})
    else:
        current = Person.objects.get(user = request.user)
        work_obj = Work.objects.get(name = wrk)
        for a in Assignment.objects.all():
            if (a.work == work_obj and a.name == asn):
                status = True
                if(a.obtained_marks == -1):
                    status = False
                    form = feedbackForm()
                    return render(request, 'give_feedback.html',{'assign':a, 'form':form, 'status':status})
                return render(request, 'give_feedback.html',{'assign':a, 'status':status})
