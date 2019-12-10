*copied from a conversation explaining this idea*

i've been looking for a script which checks for duplicate files and folders and gives me a good summary of that information

decided to write my own because I don't really know what I want especially wrt to that last point

the steps to solving this problem are therefore kinda like:
1) list the files
2) check for duplicates
3) summarize that info

im making it a bit complicated to deal with the idea that i might be running it multiple times on the same files
and also the idea that I have total like over a TB of data so it might get halfway thru and then crash or something

basically my complexity is that its designed to save its work in somewhat readable files and use that work if you ask it to run again
(unless you ask it to ignore past work and then it overwrites ofc)

im stating this like its all done but right now it just puts a list of files in every directory (the list is of the files in that directory and some other data for later comparison)

okay thats it
