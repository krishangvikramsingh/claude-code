import requests
B="http://127.0.0.1:8000"
def show(label,r):
    print(f"{label}: HTTP {r.status_code} {r.json()}")
show("GET /health",requests.get(B+"/health"))
cid=requests.get(B+"/colleges").json()[0]["id"]
show("POST /register (college email)",requests.post(B+"/register",json={"name":"Asha Rao","email":"Asha@nmims.edu.in","password":"secret123","college_id":cid}))
show("POST /register (gmail)",requests.post(B+"/register",json={"name":"Rahul","email":"rahul@gmail.com","password":"x","college_id":cid}))
show("POST /register (duplicate, other case)",requests.post(B+"/register",json={"name":"Asha","email":"asha@NMIMS.edu.in","password":"x","college_id":cid}))
tok=requests.post(B+"/login",json={"email":"asha@nmims.edu.in","password":"secret123"}).json()["token"]
print("POST /login: token issued")
show("GET /search pg_hostel",requests.get(B+"/search",params={"category":"pg_hostel","lat":19.1044,"lon":72.8365}))
show("GET /search event",requests.get(B+"/search",params={"category":"event","lat":19.1044,"lon":72.8365}))
h={"Authorization":"Bearer "+tok}
rec=requests.get(B+"/search",params={"category":"pg_hostel","lat":19.1044,"lon":72.8365}).json()["results"][0]["id"]
r=requests.post(B+"/reviews",json={"rec_id":rec,"rating":5,"comment":"Clean rooms"},headers=h); show("POST /reviews",r)
show("POST /reviews (rating 4.5)",requests.post(B+"/reviews",json={"rec_id":rec,"rating":4.5},headers=h))
rid=r.json()["review_id"]
show("validate as student",requests.post(f"{B}/reviews/{rid}/validate",json={"approve":True},headers=h))
at=requests.post(B+"/login",json={"email":"admin@platform.in","password":"admin-pass"}).json()["token"]
show("validate as admin",requests.post(f"{B}/reviews/{rid}/validate",json={"approve":True},headers={"Authorization":"Bearer "+at}))
show("GET /search pg_hostel (after validation)",requests.get(B+"/search",params={"category":"pg_hostel","lat":19.1044,"lon":72.8365}))
for i in range(5): requests.post(B+"/login",json={"email":"asha@nmims.edu.in","password":"bad"})
show("login after 5 failures",requests.post(B+"/login",json={"email":"asha@nmims.edu.in","password":"secret123"}))
