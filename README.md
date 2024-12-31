Im using this code to generate metadata CSV for Adobe Contributor Image and Video also Freepik Image Contributor. 

You must have Gemini API to use this.

How to use it
you just have to create virtual environment
then install the library using 
> python install -r requirements.txt

(p.s: usually when you install virtual environment there is option on there that put you to choose requirement.txt)
after that, go to src file then run main.py

while you inside the app
1. choose settings and set the API.
2. Go to Models and choose Gemini-1.5-flash (i already make it default but u can choose another models if you had subscription API)
3. Choose the input foler where you put the images that you want to anlyzer
4. Choose the output folder where you want to put the result of analysis
5. Upload the images on Adobe Contributor or Freepik.
6. Upload CSV File that you've been generated before. (In this case watchout for the filename, if it's not ready to submit, then there is something wrong with the filename or file format. When you analyze .png format the output of the result should be .png format too then you must upload .png format file)
7. Then you're ready to go.


you can also build the exe using
> python build_exe.py
