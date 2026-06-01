# Registration-form-for-chess
A Flask web application that lets users register for a tournament. Admin page with functions that can export all users signed up, drop the database and compare users that have signed up online and have registered on the page.

**TO RUN THE PROGRAM**
<br>
1: Download the repo <br>
2: install requierments with <br>
```bash
pip install -r requirements.txt
```
<br>
3: Run Index.py

```bash
python Index.py
```
<br>
4: localhost have opend on port 5000 where u can accsess the page.<br>

You whould need to put it behind a proxy or in some way not run it localy to use it in a real world senario.
To allow users to scan the QR code that takes them to the registration. 
### QR code that binds to host ip and redirect to /Registration
![ QR code that binds to host ip and redirect to /Registration](https://raw.githubusercontent.com/Nybbster/Registration-form-for-chess/refs/heads/main/Sk%C3%A4rmbild%202026-06-01%20120311.png)
### Login page for the admin page. (ONLY allows one Admin account
![Login page for the admin page. (ONLY allows one Admin account)](https://raw.githubusercontent.com/Nybbster/Registration-form-for-chess/refs/heads/main/Sk%C3%A4rmbild%202026-06-01%20120432.png)
### Admin page where you can go back to the QR page, export everyone that signed up to CSV, look at the entries, and drop everyone that have signed up
![Admin page where you can go back to the QR page, export everyone that signed up to CSV, look at the entries, and drop everyone that have signed up](https://raw.githubusercontent.com/Nybbster/Registration-form-for-chess/refs/heads/main/Sk%C3%A4rmbild%202026-06-01%20120519.png)
### The Show entry page where you can see and compare signed up online and signed up in person at the event.
![The Show entry page where you can see and compare signed up online and signed up in person at the event.](https://raw.githubusercontent.com/Nybbster/Registration-form-for-chess/refs/heads/main/Sk%C3%A4rmbild%202026-06-01%20120534.png) 



