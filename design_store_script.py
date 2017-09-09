"""
Python Qsys Check
Jake Bosset
Version 0.1
===============================================================================================
Usage: %prog [options]
Script to download design examples
Steps:
   1: arc shell acds/16.1
   2: arc shell python_altera/2.7.3
   3: python desing_store_script.py ....
===============================================================================================
"""

import subprocess
import os
import logging
import logging.config
import logging.handlers
import re
import copy
import shutil
import sys
import glob
import optparse


def qextract(file_path=None):
    """
    Does a qextract which extracts the .par file into a .qar
    :param file_path: path where the .par file is that needs to be extracted
    :return: a tuple of the command line output from the extract and True if the extraction was successful
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Get the name of the project from the name of the .par file we extracted earlier
    proj_name, proj_found = get_proj_name()
    # Throw an error if we cannot find a .par name
    if not proj_found:
        logging.error(proj_name)
        return proj_name, False
    # Make sure we have an extention; get_proj_name only returns the file's name not the extension
    proj_name1 = proj_name +".par"

    try:
        # Find the .par file and do a platform install from the quartus shell
        command1 = "quartus_sh --platform_install -package " + proj_name1
        cmd_output = subprocess.check_output(command1, shell=True)

        command2 = "quartus_sh --platform -name " + proj_name + "-search_path ."
        cmd_output2 = subprocess.check_output(command2, shell=True)
        #print("successful extraction")
        success = True

    except subprocess.CalledProcessError as test_except:
        # If we run into an error extracting the project, log it to the console
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred in the .par extraction: " + error_msg)
        cmd_output = test_except.output
	#print("unsuccessful extraction")
        success = False

    if success:
        logging.info("Successfully extracted .par into a .qar")
    else:
        logging.error("Error extracting .par into a .qar")

    return cmd_output, success

def get_proj_name():
    """
    Gets the project name from the .par file
    :return: a string representing the name of the project, and True if it successfully found it
    """
    par_list = []
    # First look for any .par files in the cwd
    for filename in os.listdir("."):
        if filename.endswith(".par"):
            par_list.append(filename)
    # Find where the pesky .par file is in case it is buried in a subdirectory
    if len(par_list) == 0:
        logging.info("Could not find a .par in the current working directory.  Checking subdirectories for a .par")
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in filenames:
                if filename.endswith(".par"):
                    par_list.append(filename)
    # If there is only one PAR file, just return its name and we are done
    if len(par_list) == 1:
        return par_list[0][:-4], True
    # If we cannot find a .par file, throw an error and punt (there should be 1 in the directory)
    elif len(par_list) == 0:
        message = "Error: There is no .par file found within the project structure.  Make sure there is one " \
                  "there otherwise we do not have a name for the project"
        return message, False
    # If we find multiple .par files, throw an error and punt (there really should only be 1)
    else:
        message = "Error: Multiple .par files found within the project structure.  Make sure there is only " \
                  "one or if there are more than one, the desired project is the only one in the current " \
                  "working directory"
        return message, False

class color:
	"""
	was used strictly for debugging	
	"""
	PURPLE = '\033[95m'
	CYAN = '\033[96m'
	DARKCYAN = '\033[36m'
	BLUE = '\033[94m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	RED = '\033[91m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	END = '\033[0m'

class text_files:
	"""
	creates/opens, clears and sets files to write final information to
	this information will include presence of qsys and qip files and if the qsf is configured correctly
	"""
	def __init__(self, directory1):
		self.empty_dir = directory1 + '/empty_dir.txt'
		self.yy_file_path = directory1 + '/GOOD_yes_qsys_yes_qip.txt'
		self.nn_file_path = directory1 + '/GOOD_no_qsys_no_qip.txt'
		self.yn_file_path = directory1 + '/BAD_yes_qsys_no_qip.txt'
		self.ny_file_path = directory1 + '/BAD_no_qsys_yes_qip.txt'
		self.wrong_qsf = directory1 + '/MISNAMED_QSF_yes_qsys_yes_qip.txt'
		self.bad_par = directory1 + '/bad_par.txt'
		self.upgrade_failure = directory1 + '/upgrade_failure.txt'
		
		open(self.empty_dir, 'w')
		open(self.yy_file_path, 'w')
		open(self.nn_file_path, 'w')
		open(self.ny_file_path, 'w')
		open(self.yn_file_path, 'w')
		open(self.wrong_qsf, 'w')
		open(self.bad_par, 'w')
		open(self.upgrade_failure, 'w')

def write_to_txt_files(text_files_class, state, message):
	""""
	this takes the case determined in main and writes the name of the original par to a txt file documenting it status
	"""
	tfc = text_files_class
	text1 = message
	if state == 1: #'yes qsys & yes qip':
		yy=open(tfc.yy_file_path, 'a')
		yy.write(text1)
		yy.write('\r\n')
	if state == 2: #'no qsys & yes qip':
		ny=open(tfc.ny_file_path, 'a')
		ny.write(text1)
		ny.write('\r\n')
	if state == 3: #'yes qsys & no qip':
		yn=open(tfc.yn_file_path, 'a')
		yn.write(text1)
		yn.write('\r\n')
	if state == 4: #'no qsys & no qip':
		nn=open(tfc.nn_file_path, 'a')
		nn.write(text1)
		nn.write('\r\n')
	if state == 5: #'wrong qsf (switch QSYS to QIP)':
		wr_qsf=open(tfc.wrong_qsf, 'a')
		wr_qsf.write(text1)
		wr_qsf.write('\r\n')
		
class TestClass():		
	"""
	main work of cleanup script. This will take a .par or .qar,(extract if neccessary) and begin combing through the contents
	to determine if the project was configured correctly. it will record all qsf, qip and qsys files and determine which text
	file the project should be recorded in
	"""
	def __init__(self, main_dir):
		
		#instantiate starting variables
		self.has_QIP = False
		self.has_QSYS = False
		self.end_QIP = False
		self.end_QSYS = False
		self.case = None
		self.directory = main_dir
		#self.text_class = text_class
		self.qsf_check = False
		self.qpf_name = None
		self.par_name = None
		
		#build remainder of class from commands
		self.qsf_file, self.qsf_path, self.qip_file_paths, self.qsys_check = self.initial_file_check()
		self.qpf_name, self.par_name = self.other_file_check()
		
		
		if self.qsys_check != [] :
			print(self.qsys_check)
			self.has_QSYS = True
		if self.qip_file_paths != []:
			self.has_QIP = True
			self.end_QIP, self.qsys_list = self.qip_checker()
			self.end_QSYS, self.qsys_file_paths = self.get_qsys_location()
			#print(self.qsys_file_paths)
			
	###initialy checks for presence of qsf, qip and qsys files; returns qsf path (str) and qip, qsys paths as list	
	def initial_file_check(self):
		for file in os.listdir(self.directory):
			if file.endswith('.qsf'):
				self.qsf_file = file
				self.qsf_path = self.directory + '/' + file
				
		self.qip_file_paths = [os.path.join(root,name)
			for root, dirs, files in os.walk(self.directory)
			for name in files
			if name.endswith(".qip")
		]
		self.qsys_check = [os.path.join(root,name)
			for root, dirs, files in os.walk(self.directory)
			for name in files
			if name.endswith(".qsys")	
		]
		
		for item in self.qsys_check:
			if item.endswith('.BAK.qsys'):
				self.qsys_check.remove(item)
		
		with open(self.qsf_path) as f:
			for line in f:
				#print (line)
				if '.qsys' in line:
					print ('wrong qsys found')
					#print(line)
					self.qsf_check = True
					break
		
		print ("checkpoint 1")
		return self.qsf_file, self.qsf_path, self.qip_file_paths, self.qsys_check
	
	###will return the name of the qpf and of the par
	def other_file_check(self):
		for file in os.listdir(self.directory):
			if file.endswith('.qpf'):
				self.qpf_name = file[:-4]
				print ('qpf_name:')
				print (self.qpf_name)
				#return True
			else:
				self.qpf_name = None
			if file.endswith('.par'):
				self.par_name = file[:-4]
				print ('print par name:')
				print(self.par_name)
			else:
				self.par_name = None
		
		print ('checkpoint 2')
		return self.qpf_name, self.par_name
	
	### finds the qips with the IP_TOOL_NAME 'Qsys' and returns both the qip locations and the flag for end_QIP	
	def qip_checker(self):
		length = len(self.qip_file_paths)
		#2. Check IP_TOOL_NAME
		pseudo_list = [None]*length
		flag = False
		count =0
		for x in range (0, length):
			with open(self.qip_file_paths[x]) as qipfile:
				for line in qipfile:
					#print(line)
					if 'IP_TOOL_NAME "Qsys"' in line:
						#print(list1[x])
						flag = True
						pseudo_list[count]=self.qip_file_paths[x]
						count += 1
		self.qsys_list = [None] * count
		for x in range (0, count):
			self.qsys_list[x]=pseudo_list[x]
		
		return flag, self.qsys_list

	###takes the list of qip files that specified IP_TOOL_NAME and returns only the qsys files relevant to them
	def get_qsys_location (self):
		length1 = len(self.qsys_list)
		
		for x in range (0, length1):
			self.qsys_list[x]=os.path.basename(self.qsys_list[x])

			self.qsys_list[x]= self.qsys_list[x][:-4]
			self.qsys_list[x]= self.qsys_list[x]+'.qsys'

		qsys_list_no_duplicates = set(self.qsys_list)
		qsys_list_no_duplicates = list(qsys_list_no_duplicates)
		length2 = len(qsys_list_no_duplicates)
		
		self.qsys_file_paths = [os.path.join(root,name)
			for root, dirs, files in os.walk(self.directory)
			for name in files
			for x in range (0,length2)
			if name.endswith(qsys_list_no_duplicates[x])	
		]
		if self.qsys_file_paths != []:
			flag = True
		else:
			flag = False

		return flag, self.qsys_file_paths
		
def qextract_wrapper(directory, text_class): 
	###can be used to determine if a qextract is necessary. if qextract fails it will be documented in a text file	
	if not os.path.isdir(directory):
		return False
	if not os.listdir(directory):
		empty_dir = open(text_class.empty_dir, 'a')
		empty_dir.write(directory)
		empty_dir.write('\r\n')
	for file in os.listdir(directory):
		if file.endswith('.par'):
			try:
				waste, flag = qextract(directory)
				return flag
			except:
				return False	
		return False
	return False

def case_function(file_class, main_dir): 
	###looks at the test class determined above and matches a specific case to the class
	fc = file_class
	case = 0
	identifier = ''
	if (fc.end_QIP and fc.end_QSYS):   #y_qsys_y_qip
		if fc.qsf_check == False:
			case = 1#'yes qsys & yes qip'
			""" figure out what do to with subdirectory necessity"""
			#copy_folders(main_dir)
			
		else:
			case = 5#'wrong qsf (switch QSYS to QIP)'   #wrong qsf
			identifier += 'qsf incorrect- qsys input instead of QIP'
	elif (fc.has_QIP == True and fc.end_QSYS == False):  
		if fc.has_QSYS == False :
			case = 2 #no qsys & yes qip #n_qsys_y_qip
		else:
			case = 5 #wrong setup
			identifier += 'wrong setup -check IP TOOL NAME in QIP files'
			
	elif fc.end_QIP == False:
		
		if fc.has_QSYS == True: #y_qsys_n_qip
			case = 3 #'yes qsys & no qip'
			if fc.has_QIP == True:
				identifier += 'mislabled qip'
			else:
				identifier += 'missing qip'
		else: #n_qsys_n_qip
			case = 4 #'no qsys & no qip'
	return case, identifier


def decision_tree(project_class,case):
	###takes the case determined by the case function and will update the file if able. cases 1 and 4 are updatable
	pc = project_class
	if case == 1:
		os.chdir(pc.directory)
		try:
			success = migrate(file_path=pc.directory)
			return success
		except:
			return False
	#elif case == 2:
	#
	#elif case == 3:
	if case == 4:
		os.chdir(pc.directory)
		#success = no_IP_update(pc)
		success = migrate_no_qsys(file_path=pc.directory)
		if success == False:
			command1 = 'pwd'
			cmd1_output = subprocess.check_output(command1, shell=True)
		
		return success
	return False
	


###used for debugging, not in use right now
def copy_folders(main_dir):
	#create qsys only folder
	newdir=  '/data/jbosset/NUE/test_folder/16.0/QSYS_FOLDER'
	command1 = 'cp -r ' + main_dir + ' ' + newdir
	print (command1)
	cmd1_output = subprocess.check_output(command1, shell=True)
	print(color.BOLD + 'QSYS MOVED TO SUBFOLDER' + color.END)

def project_test(main_dir, text):
	###looks for presence of par or qpf. will begin qextract_wrapper if par is present.
	#if main_dir == None:
	#	return False, False
	try:
		print('check1')
		print(main_dir)
		for file in os.listdir(main_dir):
			if file.endswith('.qpf'):
				dir_flag = True
				print('bypass qextract')
				return dir_flag, dir_flag
		print('check2')
		for file in os.listdir(main_dir):
			print(file)
			if file.endswith('.par'):
				dir_flag = True
				proceed = qextract_wrapper(main_dir, text)
				return proceed, dir_flag
	except:
		dir_flag = False
		print('not a directory')
		return dir_flag, dir_flag
	return False,False


###will report qip and qsys locations to terminal
def qsys_checker(main_dir):
	proceed, directory_flag = project_test(main_dir)
	if proceed:
		pc = TestClass(main_dir)
		relative_qsys = [os.path.relpath(path,main_dir) for path in pc.qsys_check]
		print('All QSYS paths:')
		print (relative_qsys)
		relative_qip = [os.path.relpath(path, main_dir) for path in pc.qip_file_paths]
		print('All QIP paths:')
		print(relative_qip)
		
	
def full_update_process(cwd, text):
	"""
	uses all the functions above to determine what steps need to be taken for the project files.
	will repeat all steps for each project in a subdirectory of the listed directory.
	can be called from wrapper.py
	will try to update every project possible
	"""
	upgraded = 0
	total = 0
	successful_list = []
	unsuccessful_list = []
	for item in os.listdir(cwd):
		main_dir = os.path.join(cwd, item)
		print(color.BOLD + main_dir + color.END )
		if os.path.isdir(main_dir) == True :
			print('start new dir')
			
			print(os.getcwd)
			proceed, directory_flag = project_test(main_dir, text)
			print('printing proceed flag')
			print(proceed)
			
			#begin the process for 
			if  proceed== True:
				os.chdir(main_dir)

				TC = TestClass(main_dir)
				case, identifier = case_function(TC, main_dir)
				
				message = item + identifier
				if case != 0:
					write_to_txt_files(text, case, message)
					print('yes')
				
				if case == 1 or case == 4: 
					print('total should increment')
					total = total + 1
					print (total)
					suc = decision_tree(TC,case)
					print('decision tree output:')
					print (suc)
					if suc == True :
						print('upgraded total:')
						upgraded = upgraded + 1
						print(upgraded)
						successful_list.append(item)
					else:
						failed = open(text.upgrade_failure, 'a')
						failed.write(main_dir)
						failed.write('\r\n')
						unsuccessful_list.append(item)
						#os.chdir(cwd)
					print('successful:')
					print(successful_list)
					print('unsuccessful')
					print(unsuccessful_list)
					print('exited decision tree')
				#del TC

			else:
				if directory_flag == True:
					os.chdir(cwd)
					bpf = open(text.bad_par, 'w')
					bpf.write(main_dir)
					bpf.write('\r\n')
					print('error')
					print('')
			
			if total != 0:
				success_rate = upgraded/total
				print('success_rate:')
				print(success_rate)
		
	print (upgraded)
	print (total)
	print('successful_updates:')
	print(successful_list)
	print('unsuccessful_updates:')
	print(unsuccessful_list)

def single_update_process(main_dir):
	os.chdir(main_dir)
	proceed = False
	print(color.BOLD + main_dir + color.END )
	if os.path.isdir(main_dir) == True :
		print('start new dir')
		print(os.getcwd)
		if find_all_filepaths_of_type('.qpf') != []:
			proceed = True
			print('found qpf; proceeding')
		elif find_all_filepaths_of_type('.par') != []:
			print('did not find qpf; found par, extracting')
			cmd_output, proceed = qextract(main_dir)
		#begin the process for updating
		if  proceed== True:
			TC = TestClass(main_dir)
			case, identifier = case_function(TC, main_dir)
			print( color.BOLD + 'CASE IS:' + color.END)
			print (case)
			
			if case == 1 or case == 4: 
				suc = decision_tree(TC,case)
				print('decision tree output:')
				print (suc)
				if suc == True :
					print('upgrade succeeded!')
				else:
					print('upgrade failed')
			if case == 2 or case ==3 or case ==5:
				print('incorrect file setup')


def print_qsys_location(project_class):
	pc = project_class
	print (pc.qsys_check)


def migrate(qsf_name=None, file_path=None):
    """
    Does the complete migration for a quartus project
    :param qsf_name: optional name of the .qsf file to use if there are multiple
    :param file_path: optional path/location to move to
    :return: True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # First convert the .par to a .qar
    #if not suc:
     #   return False
    #Now extract the .qar
    #cmd_output, suc = qplatform()
    #if not suc:
    #    return False
    # Make sure if there are qip files, any qsys files referenced actually exist
    #suc = does_needed_qsys_exist()
    #if not suc:
   #     return False
    # Write any files already in  filelist.txt to a temporary filelist.txt:
    print('starting migrate')
    print(file_path)
    suc = write_filelist_to_temp(file_path = file_path)
    print(color.BOLD + 'filelist_temp SUCCESSFUL' +color.END)
    if not suc:
        return False
    # Now generate files from qsys
    #suc = qsys_gen()
    #if not suc:
    #    return False
    # Now upgrade the ip cores for the project
    
	#cmd_output, suc = upgrade_ip()

    cmd_output1, suc1 = gen_ip_filelist()
    if not suc:
        return False
    print(color.BOLD + 'IP_upgrade_successful' +color.END)
	# Now generate the platform_setup.tcl, with an optional argument being the name of the .qsf file to use
    suc = q2p(qsf_name, file_path = file_path)
    if not suc:
        return False
    print(color.BOLD + 'Q2p SUCCESSFUL' +color.END)
    suc = output_file_path(file_path)
    if not suc:
        return False
    suc = qsource(file_path = file_path)
    
    if not suc:
        return False
    print(color.BOLD + 'qsource SUCCESSFUL' +color.END)
	# Write files referenced in qip files to the filelist.txt
    # Commenting this out because Sameena's script does all of this already
    # ip_files, suc = qsource_ip()
    # if not suc:
    #     logging.error("Error adding files from .qip into filelist.txt")
    #     return False
    # Do some cleaning of the filelist.txt
    print('NOW UPDATING')
    update_filelist()
    f = open('filelist.txt', 'a')
    f.write('')
    f.close()
    # Now make sure nothing illegal has been added to the filelist.txt
    print('update filelist ran')
    suc = ready_for_archive()
    if not suc:
        print('ready for archive:failed')
        return False
    # Archive the project into a .qar file
    print('NOW ARCHIVING')
    cmd_output, suc = qarchive(file_path = file_path)
    print(color.BOLD + 'qarchive SUCCESSFUL' +color.END)
    while not suc:
        if not fix_archive_errors(cmd_output):
            return False
        cmd_output, suc = qarchive(file_path = file_path)
        if not suc:
            return False
    # Create a test directory to store the project and try expanding/compiling the design there
    print('NOW TESTING')
    suc = test_proj(file_path = file_path)
	
    if not suc:
        return False
    logging.info("-------------COMPILATION SUCCESSFUL HOORAY!!!!!!---------------")
    # Go up a directory to find the QAR name
    os.chdir("..")
    qar_name, found_qar = get_qar_name()
    # If we do not find a .qar in the current directory, throw an error
    if not found_qar:
        err_msg = "The design compiled successfully but could not find a .qar in the cwd.  " \
                  "Try looking in the project directory"
        logging.error(err_msg)
        return False
    logging.info("The final packaged and updated design can be found at " + qar_name)
    print(color.BOLD + 'COMPILATION SUCCESSFUL' +color.END)
    return True

def migrate_no_qsys(qsf_name=None, file_path=None):
    """
    Does the complete migration for a quartus project
    :param qsf_name: optional name of the .qsf file to use if there are multiple
    :param file_path: optional path/location to move to
    :return: True if no errors occurred
    """
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
	
    print('starting migrate')
    suc = write_filelist_to_temp(file_path = file_path)
    print(color.BOLD + 'filelist_temp SUCCESSFUL' +color.END)
    if not suc:
        return False

    # Now generate the platform_setup.tcl, with an optional argument being the name of the .qsf file to use
    suc = q2p(qsf_name, file_path = file_path)
    if not suc:
        return False
    print(color.BOLD + 'Conversion of QSF to platformsetup.tcl SUCCESSFUL' +color.END)
    suc = output_file_path(file_path)
    if not suc:
        return False
    suc = qsource(file_path = file_path)
    if not suc:
        return False
    print(color.BOLD + 'qsource SUCCESSFUL' +color.END)
    # Write files referenced in qip files to the filelist.txt
    # Commenting this out because Sameena's script does all of this already
    # ip_files, suc = qsource_ip()
    # if not suc:
    #     logging.error("Error adding files from .qip into filelist.txt")
    #     return False
    # Do some cleaning of the filelist.txt
    print('NOW UPDATING')
    update_filelist()
    f = open('filelist.txt', 'a')
    f.write('')
    f.close()
    # Now make sure nothing illegal has been added to the filelist.txt
    suc = ready_for_archive()
    if not suc:
        return False
    # Archive the project into a .qar file
    print('NOW ARCHIVING')
    cmd_output, suc = qarchive(file_path = file_path)
    if suc:
        print(color.BOLD + 'qarchive SUCCESSFUL' +color.END)
    while not suc:
        if not fix_archive_errors(cmd_output):
            return False
        cmd_output, suc = qarchive(file_path = file_path)
        if not suc:
            return False
    # Create a test directory to store the project and try expanding/compiling the design there
    print('NOW TESTING')
    suc = test_proj(file_path = file_path)
	
    if not suc:
        return False
    logging.info("-------------COMPILATION SUCCESSFUL HOORAY!!!!!!---------------")
    # Go up a directory to find the QAR name
    os.chdir("..")
    qar_name, found_qar = get_qar_name()
    # If we do not find a .qar in the current directory, throw an error
    if not found_qar:
        err_msg = "The design compiled successfully but could not find a .qar in the cwd.  " \
                  "Try looking in the project directory"
        logging.error(err_msg)
        return False
    logging.info("The final packaged and updated design can be found at " + qar_name)
    print(color.BOLD + 'COMPILATION SUCCESSFUL' +color.END)
    return True
		

def update_filelist(file_path=None, sw_folder = None):
    """
    This function updates the filelist.txt to remove duplicates and make sure all files exist
    It also adds all files that we requested to add as stored in software or referenced in created filelist_temp
    :return: N/A
    """
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    if sw_folder == None:
        sw_folder = 'software'
    # This writes all of the extra files to the filelist.txt first (we remove duplicates later)
    # If we have a filelist_temp, then write each file inside into the filelist.txt
    filelist = open("filelist.txt", "a")
    if os.path.isfile("filelist_temp.txt"):
        filelist_temp = open("filelist_temp.txt", "r")
        files_to_add = filelist_temp.readlines()
        ii = len(files_to_add)
        for x in range (0, ii):
            filelist_write(filelist, files_to_add[x])
        #filelist.writelines(["%s" % item for item in files_to_add])
        filelist_temp.close()
    # If we have a software folder, be sure to include that as well
    if os.path.exists(sw_folder):
        software_files = list_all_files_in_directory(sw_folder)
        ii = len(software_files)
        for x in range (0, ii):
            filelist_write(filelist, software_files[x]+'\n')
        #filelist.writelines(["%s\n" % item for item in software_files])
    filelist.close()

    out = subprocess.check_output('dos2unix filelist.txt', shell=True)
    # Now get all of the lines from the filelist.txt and remove duplicates
    filelist = open("filelist.txt", "r")
    files = remove_duplicates(filelist.readlines())
    filelist.close()
    # Now only write the ones that are not duplicated
    filelist = open("filelist.txt", "w")
    for each_file in files:
        each_file_name = each_file[:-1]  # Get rid of the newline at the end of each name
        logging.debug("Found file " + each_file_name)
        if not os.path.isfile(each_file_name):
            # If the file is referenced in the platform directory but is not found there, get rid of the platform part
            # of the path
            if each_file.startswith("platform/") and os.path.isfile(each_file_name[9:]):
                #filelist.write(each_file[9:])
                filelist_write(filelist, each_file[9:])
                logging.info("Found file " + each_file_name + " but it was not in the platform directory.  "
                                                              "Removing the platform directory and continuing")
            # Ignore missing files that are not needed
            elif each_file_name.endswith((".stp", ".sdc", ".SDC", ".cmp", ".cdf", ".ppf")):
                logging.warning("Found an unneccasry file referenced in platform_setup.tcl but not found in "
                                "directory; omitting file " + each_file_name)
            # We can also ignore .qsf files that are in the root directory as they are not needed either
            elif each_file_name.endswith(".qsf") and "/" not in os.path.normpath(each_file_name):
                logging.warning(".qsf file referenced in the root directory but not found.  Omitting this file")
            # If we cannot find the file, omit it from the filelist.txt (or it will fail archive).  We will search for
            # the file at a later time if it causes an error compiling the project
            else:
                filelist_write(filelist, each_file)
                #filelist.write(each_file)
                logging.warning(
                    "File " + each_file_name + " referenced in qip but not found in its place.  "
                                               "If it is needed to run the project, please place it "
                                               "in the expected location")
        # If we found the file where it was wanted, go ahead and add it
        else:
            filelist_write(filelist, each_file)
            #filelist.write(each_file)
#	filelist.write('\n')
    filelist.close()
    return


def output_file_path(main_dir):

	if main_dir:
		os.chdir(main_dir)
	platform = open('platform_setup.tcl')
	output_dir = False
	pstcl_info =[]
	for line in platform:
		pstcl_info.append(line)
	platform.close()
	for i in pstcl_info:
		if 'set_global_assignment -name PROJECT_OUTPUT_DIRECTORY' in i:
			print ('Output directory already defined')
			output_dir= True
			if not 'set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files\n' in i:	
				f= open('platform_setup.tcl', 'w')
				for i in pstcl_info:
					if 'set_global_assignment -name PROJECT_OUTPUT_DIRECTORY' in i:
						pstcl_info.remove(i)
						f.write('set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files\n')
					else:
						f.write(i)
				f.close()
		return True
	if output_dir == False:
		input = open('platform_setup.tcl', 'a')
		input.write('set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files')
		print ('Output Directory added to platform_setup.tcl')
		input.close()
		return True
	if not os.path.isdir(main_dir):
		print('Invalid Directory')
		return False
	return True	
	

def migrate_design(file_path=None):
    """
    Wrapper around the migrate() function, which prints out some nice stuff in addition to performing the migration
    :param file_path: optional path/location to move to
    :return: Nothing
    """

    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Setup logging config for both file and console:
    logging_config('migration_result.log')

    suc = migrate()
    if suc:
        success_string = "\n\n***************************MIGRATION SUCCESSFUL!!!*********************************"
        # print success_string
        logging.info(success_string)
    else:
        fail_string = "\n\n------------------------------MIGRATION FAILED :(-----------------------------------"
        # print fail_string
        logging.info(fail_string)
    return


def migrate_specify_qsf(qsf_name, file_path=None):
    """
    Wrapper around the migrate() function, which prints out some nice stuff in addition to performing the migration
    :param qsf_name: name of the .qsf file to
    :param file_path: optional path/location to move to
    :return: Nothing
    """

    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Setup logging config for both file and console:
    logging_config('migration_result.log')

    # If the person called the file by name instead of by path
    if not qsf_name.endswith(".qsf"):
        qsf_name += ".qsf"
    suc = migrate(qsf_name)
    if suc:
        success_string = "\n\n***************************MIGRATION SUCCESSFUL!!!*********************************"
        logging.info(success_string)
    else:
        fail_string = "\n\n------------------------------MIGRATION FAILED :(-----------------------------------"
        logging.info(fail_string)
    return


def archive_design(file_path=None):
    """
    Does the full archive for a quartus project
    :param file_path: optional path/location to move to
    :return: True if no errors occurred and the project was archived successfully
    """

    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Setup logging config for both file and console:
    logging_config('archive_result.log')

    # Do the actual migration
    suc = archive_internal()
    if suc:
        success_string = "\n\n***************************ARCHIVE SUCCESSFUL!!!*********************************"
        # print success_string
        logging.info(success_string)
    else:
        fail_string = "\n\n------------------------------ARCHIVE FAILED :(-----------------------------------"
        # print fail_string
        logging.info(fail_string)
    return


def archive_specify_qsf(qsf_name, file_path=None):
    """
    Does the full archive for a quartus project
    :param qsf_name: name of the .qsf file to use when archiving
    :param file_path: optional path/location to move to
    :return: True if no errors occurred and the project was archived successfully
    """
    # If we pass a location to move to, change directory to said location
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Setup logging config for both file and console:
    logging_config('archive_result.log')

    # If the person called the file by name instead of with the correct extension
    if not qsf_name.endswith(".qsf"):
        qsf_name += ".qsf"

    # Perform the actual migration
    suc = archive_internal(qsf_name)
    if suc:
        success_string = "\n\n***************************ARCHIVE SUCCESSFUL!!!*********************************"
        logging.info(success_string)
    else:
        fail_string = "\n\n------------------------------ARCHIVE FAILED :(-----------------------------------"
        logging.info(fail_string)
    return


def archive_internal(qsf_name=None, file_path=None):
    """
    Internal nuts-and-bolts archive of a quartus project
    :param qsf_name: optional name of the .qsf file to use if there are multiple
    :param file_path: optional path/location to move to
    :return: True if no errors occurred and the project was archived successfully
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # First extract any existing .par that is already there
    cmd_output, suc = qrestore()
    if not suc:
        return False
    # Now generate files from qsys
    suc = qsys_gen()
    if not suc:
        return False
    # Now upgrade the ip cores for the project, fist by getting the name of the .qpf
    qpf_name, suc = get_qpf_name()
    if not suc:
        return False
    cmd_output, suc = upgrade_ip(qpf_name)
    if not suc:
        return False
    # First generate the platform_setup.tcl
    suc = q2p(qsf_name)
    if not suc:
        return False
    # Make sure if there are qip files, any qsys files referenced actually exist
    suc = does_needed_qsys_exist()
    if not suc:
        return False
    # Write all the files already in the filelist to a temporary location so we can write over the filelist.txt
    suc = write_filelist_to_temp()
    if not suc:
        return False
    # Now add all the IP from the platform_setup.tcl and .qip files
    suc = qsource()
    if not suc:
        return False
    # Do some cleaning of the filelist.txt
    update_filelist()
    # Now make sure nothing illegal has been added to the filelist.txt
    suc = ready_for_archive()
    if not suc:
        return False
    # Archive the project into a .qar file
    cmd_output, suc = qarchive_package()
    while not suc:
        if not fix_archive_errors(cmd_output):
            return False
        cmd_output, suc = qarchive_package()
    # Create a test directory to store the project and try expanding/compiling the design there
    suc = test_proj()
    if not suc:
        return False
    logging.info("-------------COMPILATION SUCCESSFUL HOORAY!!!!!!---------------")
    # Go up a directory to find the QAR name
    os.chdir("..")
    qar_name, found_qar = get_qar_name()
    # If we do not find a .qar in the current directory, throw an error
    if not found_qar:
        err_msg = "The design compiled successfully but could not find a .qar in the cwd.  " \
                  "Try looking in the project directory"
        logging.error(err_msg)
        return False
    # Give the location of the archived design
    archive_location = "****************************************************************\n The archived design can " \
                       "be found at " + qar_name + "\n****************************************************************"
    logging.info(archive_location)
    print archive_location

    return True


def write_filelist_to_temp(file_path=None):
    """
    This function writes all the lines from filelist.txt into filelist_temp.txt
    Used only for migration; where someone's design may include a filelist already
    :return: True if filelist_temp was successfully written to
    """
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # This writes all of the starting files in filelist.txt (we remove duplicates later) to filelist_temp.txt
    if os.path.isfile("filelist.txt"):
        filelist_temp = open("filelist_temp.txt", "w")  # Changing this to "write" mode so it always overwrites
        # (a+ before)
        filelist = open("filelist.txt", "r")
        all_files_to_add = filelist.readlines()
        # Get rid of anything illegal in the filelist.txt
        files_to_add = []
        illegal_files = ["top.qsf", "top.qpf"]
        for each_file in all_files_to_add:
            # Do not add anything that is included in the illegal_files.
            legit_file = True
            for ill_file in illegal_files:
                # Also make sure we are not including anythig in the db directory
                if ill_file in each_file or each_file.startswith("db/"):
                    # In this case, we do not want to add any bad files to the filelist if they are already there
                    logging.warning("File " + each_file[:-1] + " included in filelist.txt but it shouldn't be.  "
                                                               "Ignoring")
                    legit_file = False
            if legit_file:
                files_to_add.append(each_file)
        # Now write all of the non-illegal files to the filelist.txt
        #filelist_temp.writelines(["%s" % item for item in files_to_add])
        ii = len(files_to_add)
        for x in range (0, ii):
            filelist_write(filelist_temp, files_to_add[x])
        filelist.close()
        filelist_temp.close()
        # Forcing this to be true unless we run into an issue where we may want this function to fail
        suc = True
        if suc:
            logging.info("Successfully wrote everything from filelist.txt to filelist_temp.txt")
        else:
            logging.error("Error writing existing files in filelist_temp to filelist.txt")
        return suc
    # If we don't have an existing filelist, we can skip this step
    else:
        logging.info("No existing filelist.txt found; generating one from IP")
        return True


def recompile(file_path=None):
    """
    Re-archives the design and runs the test again, useful for when errors have occurred
    :param file_path: optional path to perform the recompilation (if in the test directory, use ..)
    :return: True if the recompilation was successful
    """
    logging.info("Attempting to recompile the design")
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # Upgrade the ip cores for the project
    cmd_output, suc = upgrade_ip()
    if not suc:
        return False
    # Regenerate all IP from the .qsys files
    suc = qsys_gen()
    if not suc:
        return False
    # Write files referenced in qip files to the filelist.txt
    suc = qsource()
    if not suc:
        return False
    # Do some cleaning up in the filelist.txt
    update_filelist()
    # Now re-archive the design
    cmd_output, suc = qarchive()
    # Keep fixing errors in archive if we keep finding them
    while not suc:
        if not fix_archive_errors(cmd_output):
            return False
        # Try archiving again after fixing an error.
        cmd_output, suc = qarchive()
    # This step creates a "test" directory and tries extracting/compiling the project
    suc = test_proj()
    if not suc:
        return False
    return True

	
def test_proj(file_path=None):
    """
    Tests the given project by creating a test directory and trying to extract and compile it
    :param file_path: optional path/location to move to
    :return: True if the test/complication was successful
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Create a test directory
    suc = create_test_dir()
    if not suc:
        return False
    # Change directory to test directory
    os.chdir("test")
    # Now platform extract the .qar
    cmd_output, suc = qplatform()
    if not suc:
        return False
    # Try compiling the design
    cmd_output, suc = qcompile()

    # Recursively fix errors in compilation as we keep finding new ones
    if not suc:
        logging.info("Trying to fix potential errors in compilation.  Changing directory out of test")
        os.chdir("..")
        if fix_compile_errors(cmd_output):
            return recompile()
        return False
    return True

	
def create_test_dir(file_path=None):
    """
    Creates a testing directory for the project
    :param file_path: file_path: optional path/location to move to
    :return: True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Create a new test directory to store the archived project, and remove anything inside previously
    remove_folder("test")
    os.makedirs("test")
    # Make sure there is only one .qar file
    qsf_list = find_local_filepaths_of_type(".qar")
    # If we cannot find a .qpf file, throw an error and punt (there should be 1 in the directory)
    if len(qsf_list) == 0:
        logging.error("Error generating test directory: No .qar file found.  Make sure you are working "
                      "in the same directory or that qarchvie worked successfully.")
        return False
    # If there is only one .qpf file, then this is what we want and we can continue
    if len(qsf_list) == 1:
        qar = qsf_list[0]
    # If we find multiple .qpf files, throw an error and punt (there really should only be 1)
    else:
        logging.error("Error generating test directory: Multiple .qar files found; not sure which one to test.  "
                      "Make sure there is only one in the current working directory.")
        return False
    # Copy the .qar file into the newly created test directory, and continue
    shutil.copyfile(qar, "test/" + qar)
    logging.info("test directory created and .qar found successfully")
    return True


	
# Original Command: #!/bin/csh -f set dest = `echo *.qar | sed 's/.qar//'`; quartus_sh
# --platform -name $dest -search_path \.
def qplatform(file_path=None):
    """
    Does a platform extract of the .qar project located in file_path
    :param file_path: path/location of "top" design to extract
    :return: A Tuple of the command line result of the platform extract and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Find where the pesky .qar file is in case it is buried in a subdirectory
    qar_list = find_all_filepaths_of_type(".qar")
    command = "quartus_sh --platform -name " + qar_list[0]

    try:
        # Try performing the platform extraction on the given file
        cmd_output = subprocess.check_output(command, shell=True)
        success = True
        logging.debug(cmd_output)
    except subprocess.CalledProcessError as test_except:
        #  If we run into an error extracting the project, log it to the console
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred in platform extraction: " + error_msg)
        success = False
        cmd_output = test_except.output
        logging.error(cmd_output)

    # No need to log the error if we didn't encounter one
    if success:
        logging.info("Successfully performed platform extraction of .qar file")
    else:
        logging.error("Error performing the platform extract of the .qar file")
    return cmd_output, success

	
def qrestore(file_path=None):
    """
    Does a restoration of a .qar project located in file_path
    :param file_path: path/location of "top" design to extract
    :return: A Tuple of the command line result of the platform extract and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Find where the pesky .qar file is in case it is buried in a subdirectory
    qar_list = find_all_filepaths_of_type(".qar")
    if not qar_list:
        logging.debug("No .qar file(s) found")
        return "", True
    command = "quartus_sh --restore -name " + qar_list[0]
    logging.info("Found a .qar file in the project, performing restoration/extraction on " + str(qar_list[0]))

    try:
        # Try performing the quartus shell extraction on a found .qar
        cmd_output = subprocess.check_output(command, shell=True)
        success = True
        logging.debug(cmd_output)
    except subprocess.CalledProcessError as test_except:
        # If we run into an error extracting/installing the project, log it to the console
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred restoring the .qar: " + error_msg)
        success = False
        cmd_output = test_except.output
        logging.error(cmd_output)

    # No need to log the error if we didn't encounter one
    if success:
        logging.info("Successfully restored .qar project")
    else:
        logging.error("Error performing the restoration of the .qar file")
    return cmd_output, success

	
def q2p(qsf_name=None, file_path=None):
    """
    Creates a platform_setup.tcl from the given .qar file
    :param qsf_name: name of the .qsf file to generate the platform_set.tcl from; otherwise it will
    use the one in the cwd
    :param file_path: optional path/location to move to
    :return: True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # If we are given a .qsf name generate the platform_setup.tcl from that
    if qsf_name:
        # Make sure the .qsf file specified is a correct path
        if not os.path.isfile(qsf_name):
            logging.error("No .qsf file with name " + qsf_name + " found in the directory.  Please choose a valid .qsf "
                                                                 "name or choose the directory this .qsf is in.")
            return False
        # Perform q2p on the given file
        return q2p_specific(qsf_name)

    # If we are not given the name of a .qsf file, search for one in the project directory
    # Make sure there is only one .qsf file in the local directory
    qsf_list = find_local_filepaths_of_type(".qsf")
    # If there are no .qsf files in the directory, throw an error

    if len(qsf_list) == 0:
        logging.error("Error: No .qsf file found.  Make sure the .qar extracted successfully "
                      "and the project has a .qsf file")
        return False
    # If there is exactly one .qsf file in the directory, create the platform_setup.tcl from this file
    # (via q2p_specific)
    if len(qsf_list) == 1:
        qsf = qsf_list[0]
    # If we find multiple .qsf files, tell the user to call specific archive or migrate functions
    else:
        logging.error("Error: Multiple .qsf files found:  " + str(qsf_list) +
                      " Make sure to place the project to its own directory so the desired qsf file is converted "
                      "to a platform_setup.tcl.  If the design you are trying to migrate has multiple .qsf files in "
                      "the project directory, choose one of the list .qsf files and call migrate_specify_qsf(), "
                      "where the first argument is the the name of "
                      "the \"top\" qsf file that you are wanting to migrate.  \nLikewise, if you are trying to "
                      "archive a design with more than one .qsf file in the project directory, use the "
                      "archive_specify_qpf() command, where the first argument is the the name of the \"top\" qsf file "
                      "that you are wanting to archive.")
        return False
    return q2p_specific(qsf)

	
def q2p_specific(qsf_name):
    """
    Creates a platform_setup.tcl from the given .qar file
    :param qsf_name: optional path/location to move to
    :return: True if no errors occurred
    """
    # Make sure the output files directory is correctly specified
    add_output_files_to_qsf(qsf_name)
    try:
        fin = open(qsf_name, 'r')
    except IOError:
        logging.error("Cannot open .qsf file!")
        return False
    # Write copy the .qsf file into a platform_setup.tcl with appropriate headers
    fout = open("platform_setup.tcl", 'w+')
    fout.write('proc ::setup_project {} {\n')
    fout.write(fin.read())
    fout.write('\n}')
    fout.close()
    fin.close()
    # If we get here, then we successfully generated the platform_setup.tcl
    success = True
    if success:
        logging.info("Successfully converted .qsf into a platform_setup.tcl")
    else:
        logging.error("Error generating platform_setup.tcl from the .qsf file")
    return success

	
def add_output_files_to_qsf(qsf_path):
    """
    Adds the output_files assignment to the .qsf file if it is not already there
    :param qsf_path: path to the .qsf file to modify
    :return: N/A
    """
    # The line we need to add to specify where to place output files
    output_files = "set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files"
    # Make sure this line is not already in the .qsf file
    qsf_file = open(qsf_path, 'r')
    qsf_lines = qsf_file.readlines()
    # If we found the line in the .qsf, then do nt write it
    found = any(output_files in line for line in qsf_lines)
    qsf_file.close()
    # If the line is not found in the .qsf file, write it
    if not found:
        logging.info("Output files path not specified or specified to an incorrect location; changing location of "
                     "output files to output_files directory.")
        qsf_file = open(qsf_path, 'a')
        qsf_file.write("\n" + output_files + "\n")
        qsf_file.close()
    return

	
def does_needed_qsys_exist():
    """
    Decides whether or not the qip needs a qsys file
    :return: True if the qip needs a qsys file, False if not
    """
    # First check to see if any .qsys files exist in the project
    qsys_list = find_all_filepaths_of_type(".qsys")
    if len(qsys_list) > 0:
        # If we find qsys file, then no need to check if one is referenced
        logging.info("Found .qsys file(s) in the project, so no need to check if one is referenced by .qip because ")
        return True
    # Get a list of all of the .qip files
    qip_list = find_all_filepaths_of_type(".qip")
    logging.debug("No .qsys file found, checking to see if the .qip files reference one")
    # Make sure each .qip doesn't need a .qsys file since we did not find a .qsys file
    for each_qip in qip_list:
        qip_file = open(each_qip, "r")
        for line in qip_file.readlines():
            if "-name IP_TOOL_ENV \"Qsys\"" in line:
                # This means the .qip file was generated from a .qsys file but the .qsys file was not in the project
                qip_file.close()
                logging.error("Could not find a Qsys file, even though one was referenced in the .qip.  Place the "
                              "needed .qsys file in the project.")
                return False
            elif "-name IP_TOOL_NAME" in line:
                continue
        qip_file.close()
    # If we get here, then we found a qsys file
    logging.info("The .qip files do not reference a .qsys file, so no .qsys is needed.")
    return True

	
def qsys_gen(file_path=None):
    """
    Generates all of the qip from the provided qsys file using the Quartus Shell
    :param file_path: optional path/location to move to
    :return: True of no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # Now find all the local .qsys files
    qsys_list = find_all_filepaths_of_type(".qsys")
    for each_path in qsys_list:
        # Skip over all of the .BAK files
        if each_path.endswith(".BAK.qsys"):
            continue
        try:
            # For each .qsys file, regenerate all of the IP inside
            command = "qsys-generate " + each_path + " --synthesis=VERILOG"
            out = subprocess.check_output(command, shell=True)
            logging.info("Qsys IP generation executed successfully for " + each_path)
            logging.debug(out)
        except subprocess.CalledProcessError as test_except:
            # If we run into an issue generating the IP from .qsys files, log the error
            error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
            logging.error("An error occurred when generating IP from the qsys file(s): " + error_msg)
            out = test_except.output
            logging.info(out)
            logging.error("Error generating IP from qsys file(s)")
            if file_path:
                logging.debug("Changing directory to " + file_path)
                os.chdir('..')
            return False
    # If we get this far, that means that the qsys generate was successful for all qsys files and we are done :)
    logging.info("Successfully generated all of the ip from the qsys file(s)!")
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir('..')
	return True


def filelist_write(filelist, location):
	location_basename = os.path.basename(location)
	if location.endswith('.qpf'):
		return True	
	if not '.' in location:
		return True
	if '/./' in location:
		if not '$' in location:
			new_loc =location.replace('/./', '/')
			filelist.write(new_loc)
			return True
		else:
			location = location.replace('/./', '/')
	if location.startswith('./'):
		if not '$' in location:
			new_loc =location.replace('./', '')
			filelist.write(new_loc)
			return True
		else:
			location = location.replace('./', '')
	#if location.startswith('platform/'):
		#if not '$' in location:
		#	new_loc =location.replace('platform/', '')
		#	filelist.write(new_loc)
		#	return True
		#else:
		#	location = location.replace('platform/', '')
		#return True;
	if '$' in location[0]:
		files= find_specific_file(location_basename)
		for file in files:
			filelist.write(file)
		return True
	else:
		filelist.write(location)
		return True

def qsource(file_path=None):
    """
    Sameena's Script
    Finds all of the required files from the platform_setup.tcl and writes them to filelist.txt
    :param file_path: optional path/location to move to
    :return: True of no errors occurred
    """

    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # Now create the filelist.txt (changed from "r" to "a" to not overwrite anything already there)
    filelist = open('filelist.txt', 'w')
    # We always want to add the platform_setup and filelist to the filelist so they are archived
    filelist.write("platform_setup.tcl\n")
    filelist.write("filelist.txt\n")
    # Now search for the .tcl file that contains the location of the .qip files to search
    for root, dirs, files in os.walk(".", topdown=True):
        for each_file in files:
            if each_file.endswith(".tcl"):
                logging.debug("Found .tcl file: " + each_file)
                # Open each .tcl file, and find the files inside
                datafile = open(os.path.join(root,each_file))
                for line in datafile:
                    # If we have a misc file, then only include it if it exists
                    if re.search("MISC_FILE", line):
                        #print("checkA")	
                        try:
                            location = line.split("FILE ")[1].split()[0]+ "\n"
                            location = location.replace('"', "")
                        # If there is no file in the line, go to the next line
                        except IndexError:
                            logging.info("Tried to scan line " + line + " for a file but no file was found.  "
                                                                        "Continuing")
                            continue
                        if not os.path.isfile(location):
                            logging.warning("Found misc file " + location + ", but it is not found it the location."
                                                                            "  Ignoring this file since it is a misc "
                                                                            "file.")
                            continue					
                            filelist_write(filelist, location)
 ####                       filelist.write(location)
                    if re.search("source", line):
                        #print("checkB")
                        try:
                            location = line.split("source ")[1].split()[0] + "\n"
                            location = location.replace('"', "")
                            filelist_write(filelist, location)
 #####                          filelist.write(location)
                        # If there is no file in the line, go to the next line
                        except IndexError:
                            logging.info("Tried to scan line " + line + " for a file but no file was found.  "
                                                                        "Continuing")
                            continue
                        #if not os.path.isfile(qsflocation):
                         #   logging.warning("Found misc file " + os.getcwd() + location + ", but it is not found at the location."
                          #                                                  "  Ignoring this file since it is a misc "
                           ##continue											
                    if re.search("FILE", line):
                        #print("checkC")
                        # TODO: Perhaps add logic to ignore HEX Generation files; ask Larry
                        try:
                            # Get the location/name of the referenced file from after the "FILE"
                            location = line.split("FILE ")[1].split()[0] + "\n"
                            location = location.replace('"', "")
                        # If there is no file in the line, go to the next line
                        except IndexError:
                            logging.info("Tried to scan line " + line + " for a file but no file was found.  "
                                                                        "Continuing")
                            continue
                        logging.debug("Location = " + location[:-1])
                        # If we have a .stp or .sdc file, only include it if it can be found
                        if re.search(".stp" or ".sdc", location) and not os.path.isfile(location):
                            logging.info("Found .stp file referenced in platform_setup.tcl but not found in directory; "
                                         "omitting file " + location)
                            #continue
                        # If a file is included in the line, write it to the filelist.txt
                        else:
                            filelist_write(filelist, location)
####						filelist.write(location)
                    # If we run into a .qip file, then add it to the list of files we are crawling through
                    if re.search("QIP_FILE", line):
                        #print("checkD")
                        # This holds the entire file path of the .qip file
                        qiplocation_temp = line.split("FILE ")[1]
                        # This holds the location of where the .qip  is
                        qippath = qiplocation_temp.split()[0]
                        logging.debug("qippath = " + qippath)
                        qiplocation = qiplocation_temp.rsplit("\n", 1)
                        logging.debug("qiplocation = " + str(qiplocation))
                        if qippath[0] == '$':
                            qip_base = os.path.basename(qippath)
                            qip_locations=find_specific_file(qip_base)
                            try:
                                qippath = qip_locations[0]
                            except IOError:
                                path_to_qip = os.getcwd() + "/" + qippath
                                logging.error("Qip file " + path_to_qip + " referenced but not found. "
                                                                          "Make sure this .qip file is either in"
                                                                          "the project directory by copying it "
                                                                          "there or remove the line referencing "
                                                                          "this file from the .qsf file, "
                                                                          "filelist.txt, or other .qip file(s)")
                                return False
                        # Open each qip file and write the needed files to filelist.txt
                        try:
                            qipdata = open(os.getcwd() + "/" + qippath, 'r')
                        except IOError:
                            if qippath.startswith("platform"):
                                qippath = qippath[9:]
                                # If the qippath is supposed to be in the platform directory, look for it there
                                try:
                                    qipdata = open(os.getcwd() + "/" + qippath, 'r')
                                # If the path to the qip referenced in the platform_setup.tcl is not actually there.
                                except IOError:
                                    path_to_qip = os.getcwd() + "/" + qippath
                                    logging.error("Qip file " + path_to_qip + " referenced but not found. "
                                                                              "Make sure this .qip file is either in"
                                                                              "the project directory by copying it "
                                                                              "there or remove the line referencing "
                                                                              "this file from the .qsf file, "
                                                                              "filelist.txt, or other .qip file(s)")
                                    return False
                            # If the .qip file does not start with the platform folder, then it is not in the correct
                            # location or not included in the project, so throw an error
                            else:
                                path_to_qip = os.getcwd() + "/" + qippath
                                logging.error("Qip file " + path_to_qip + " referenced but not found. "
                                                                          "Make sure this .qip file is either in"
                                                                          "the project directory by copying it "
                                                                          "there or remove the line referencing "
                                                                          "this file from the .qsf file, "
                                                                          "filelist.txt, or other .qip file(s)")                                
                                return False
                        # Go through each line inside the .qip file and look for more source files
                        for qip_line in qipdata:
                            #print("checkE")
                            # Add a "." to the beginning of the line so we cannot run into an error splitting the path
                            qippath_mod = "./" + qippath
                            qippath_mod = qippath_mod.rsplit("/", 1)[0]
                            # Find each line in the .qip file that starts with "FILE"
                            if re.search("FILE", qip_line):
                                # QipSource holds each ip file relative to the location of the qip file
                                try:
                                    qipsource = qip_line.split("(qip_path) ")[1]
                                # If we do not have a location relative to the .qip path, then use the absolute path
                                except IndexError:
                                    qipsource = qip_line.split("\"")[1]
                                # Replace all of the brackets and quotes with nothing
                                qipsource = re.sub(']', '', qipsource)
                                qipsource = re.sub('"', '', qipsource)
                                # Now get rid of all of the shit in the qippath
                                qipsource_split = qipsource.split("/")
                                # Simplify the path to each source file by getting rid of redundancies in the file path
                                count = 0
                                for x in qipsource_split:
                                    if x == '..':
                                        count += 1
                                qippath_mod = qippath_mod.rsplit("/", count)[0]
                                qippath_mod += "/"
                                qipsource = qipsource.replace("../", "")
                                # Join the path and name of the file to get the full location
                                # logging.debug("qipsource = " + qipsource[:-1]) # 2 before the colin
                                # logging.debug("qippath_mod = " + qippath_mod[2:])
####                                filelist.write(qippath_mod[2:] + qipsource)
                                filelist_write(filelist, qippath_mod[2:] + qipsource)
                                logging.debug("writing path" + qippath_mod[2:] + qipsource[:-1])
                        qipdata.close()
                datafile.close()
                datafile = None
    if os.path.isfile('filelist_ip.txt'):
        with open('filelist_ip.txt') as f:
            for line in f:
                #print (line)
                filelist_write(filelist, line)
####				filelist.write(line)
        f.close()
    filelist.close()
    # In case we have a reason for this to break, we can return False, but right now this does not fail
    success = True
    if success:
        logging.info("Successfully wrote all of the IP and QIP files to the filelist.txt")
    else:
        logging.error("Error writing IP and QIP files to the filelist.txt")
    return success


			
def build_filelist(main_dir, sw_folder, qsf_name=None, file_path=None, proj_name = None):
    os.chdir(main_dir)
    #suc = write_filelist_to_temp(file_path)
   # if not suc:
    #    return False
    if os.path.isfile('filelist_temp.txt'):
        os.remove('filelist_temp.txt')
    # Now generate the platform_setup.tcl, with an optional argument being the name of the .qsf file to use
    suc = q2p(qsf_name, file_path = file_path)
    if not suc:
        return False
    print(color.BOLD + 'Conversion of QSF to platformsetup.tcl SUCCESSFUL' +color.END)
    suc = output_file_path(file_path)
    if not suc:
        return False
    suc = qsource(file_path)
    if not suc:
        return False
    print(color.BOLD + 'qsource SUCCESSFUL' +color.END)
	# Write files referenced in qip files to the filelist.txt
    # Commenting this out because Sameena's script does all of this already
    # ip_files, suc = qsource_ip()
    # if not suc:
    #     logging.error("Error adding files from .qip into filelist.txt")
    #     return False
    # Do some cleaning of the filelist.txt
    print(os.getcwd())
    print('now updating filelist')
    update_filelist(file_path = file_path, sw_folder=sw_folder)
    # Now make sure nothing illegal has been added to the filelist.txt
    suc = ready_for_archive()
    if not suc:
        print('failed')
        return False
    # Archive the project into a .qar file
    cmd_output, suc = qarchive(file_path, proj_name)
    while not suc:
        if not fix_archive_errors(cmd_output):
            return False
        cmd_output, suc = qarchive(file_path)
    print(color.BOLD + 'qarchive SUCCESSFUL' +color.END)
	# Create a test directory to store the project and try expanding/compiling the design there
    suc = test_proj(file_path)
    if not suc:
        return False
    print('build full packager, qcompile successful')
    logging.info("-------------COMPILATION SUCCESSFUL HOORAY!!!!!!---------------")
	
	
def qsource_ip(file_path=None):
    """
    Gets a list of all of the source IP files by looking through qip files, and writes them to filelist.txt
    :param file_path: path where the project is located
    :return: a list of all of the ip files, and True if successful
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # First get a list of all of the source files referenced in the .qip
    ip_files, suc = find_all_qip_ip()
    if not suc:
        logging.error("Error finding all of the ip files from the .qip files")
        return ip_files, False
    # Now write each of these source files to the filelist.txt
    suc = write_source_ip_to_filelist(ip_files)
    if not suc:
        return ip_files, False
    return ip_files, suc

	
def find_all_qip_ip():
    """
    Gets a list of all of the source IP files in each of the qip files
    :return: a List of all of the ip files
    """
    # First get all the qip files to find references
    qip_files = find_all_filepaths_of_type(".qip")

    ip_files = copy.deepcopy(qip_files)
    logging.info("Qip files = " + str(qip_files))
    # Add the ip files from each of the qip files
    for each_qip in qip_files:
        ip_files.extend(find_ip_from_qip(each_qip))
    # Remove duplicates from the list:
    ip_files = list(set(ip_files))
    return ip_files, True

	
def find_ip_from_qip(qip_path):
    """
    Returns a list of all of the files referenced in the given qip file
    :param qip_path: a path to a qip file
    :return: a list of all of the files referenced in the qip file
    """
    ip_list = []
    # We really should not ever get this error, but if we do be sure to tell the user what is going on
    if not os.path.isfile(qip_path):
        logging.error("No qip file found at " + qip_path)
        return ip_list
    qip_file = open(qip_path, "r")
    # Files usually have the name "_FILE" and then the path in quotes after
    find_files = re.compile("_FILE[^\"]*(\"[^\"]+\")")
    # Find all of the files in each of the qip_file lines
    for line in qip_file:
        pat = find_files.search(line)
        # Add the filename to the list of ip_files if it exists
        if pat:
            # If the path is found, since it is given relative to the qip, join the qip path and relative path
            full_path = os.path.join(os.path.dirname(qip_path), pat.group(1)[1:-1])
            ip_list.append(os.path.normpath(full_path))
    qip_file.close()
    return ip_list

	
def write_source_ip_to_filelist(ip_list):
    """
    Writes the given list of ip file paths to filelist.txt
    :param ip_list: A list of the ip files to write to the filelist.txt
    :return: True if the write was successful
    """
    # Keep track of the files to add
    files_to_add = copy.deepcopy(ip_list)
    if os.path.isfile("filelist.txt"):
        logging.info("Found existing filelist.txt; appending to the end of it")
        filelist = open("filelist.txt", "r+")
        # Remove files already in filelist.txt from the list of files to add
        for file_line in filelist:
            for ip_line in ip_list:
                try:
                    # If we get a collision between files, don't add the duplicate
                    if os.path.samefile(file_line[:-1], ip_line):
                        logging.debug(ip_line + " is already in filelist.txt")
                        # Remove the existing file from the list of files to add because it was already found
                        if ip_line in files_to_add:
                            files_to_add.remove(ip_line)
                except OSError:
                    # If a file is not present, do not add it to e filelist.txt, as it will fail the archive
                    if not os.path.isfile(file_line):
                        logging.warning(
                            "Be careful, " + file_line + " not found in the directory. Be sure it is in the location "
                                                         "specified or it will not be added and the project"
                                                         " may not compile")
                        break
                    # This is a redundancy check, as we should never get here
                    else:
                        logging.warning(
                            "Be careful, " + ip_line + " not found in the directory. Be sure it is in the location "
                                                       "specified or it will not be added and the project "
                                                       "may not compile")
                        continue

    else:
        # Sameena's script should have created a filelist.txt, so throw a warning if this is not the case
        logging.warning(
            "No filelist.txt found; creating one.  Be careful because non-ip source files may not be added. "
            "Check the directory to be sure or add the filelist.txt created by qSource!")
        filelist = open("filelist.txt", "a+")
    # Write files to the filelist.txt
	
	###filter the files_to add list
    ii = len(files_to_add)
    for x in range (0, ii):
        filelist_write(filelist, files_to_add[x])

#    filelist.writelines(["%s\n" % item for item in files_to_add])
    filelist.close()
    return True

	
def write_files_to_filelist(files):
    """
    Writes the given list of files to filelist_temp.txt.  Throws an error if they were already added
    :param files: A list of the ip files to write to the filelist_temp.txt
    :return: True if the write was successful
    """
    # Keep track of the files to add
    files_to_add = copy.deepcopy(files)
    filelist_temp = open("filelist_temp.txt", "a+")
    # Remove files already in filelist_temp.txt from the list of files to add
    for file_line in filelist_temp:
        for each_file in files:
            try:
                # If we get a collision between files, don't add the duplicate
                if os.path.samefile(file_line, each_file):
                    logging.debug(each_file + " is already in filelist_temp.txt")
                    # If the file is already in our list of files we need to add, be sure we do not write it again
                    if each_file in files_to_add:
                        files_to_add.remove(each_file)
            except OSError:
                if not os.path.isfile(file_line):
                    # If one of our files does not exist, log a warning
                    logging.warning(
                        "Be careful, " + file_line + " not found in the directory. Be sure it is in the "
                                                     "location specified or it will not be added and the project "
                                                     "may not compile")
                    break
                else:
                    logging.warning(
                        "Be careful, " + each_file + " not found in the directory. Be sure it is in the"
                                                     " location specified or it will not be added and the project"
                                                     " may not compile")
                    continue

    if not files_to_add:
        logging.error("All files we found to add were already in the filelist_temp.txt")
        return False
    # Write files to list
    ii = len(files_to_add)
    for x in range (0, ii):
        filelist_write(filelist_temp, files_to_add[x])
	#    filelist_temp.writelines(["%s\n" % item for item in files_to_add])
    filelist_temp.close()
    return True

	
def ready_for_archive():
    """
    Makes sure the given file is ready for archiving by checking for illegal names and other bad shit
    :return: True if it is ready, False if not
    """
    filelist = open("filelist.txt", "r")
    filelist_files = filelist.readlines()
    illegal_files = ["top.qsf", "top.qpf"]
    # Make sure each line in the filelist.txt does not refer to a file which would be overwritten by the compilation
    for filelist_line in filelist_files:
        for line in illegal_files:
            # Make sure each line in the filelist does not contain anything illegal or references anything in the db
            if line in filelist_line or filelist_line.startswith("db/"):
                logging.error("File " + line + " included in filelist.txt but it shouldn't be")
                filelist.close()
                # Print error message if we encounter bad files in the filelist, then punt
                logging.error(
                    "Some illegal files were added to the filelist.txt.  Make sure that anything in the db/ folder "
                    "is not included in the filelist.txt.  Also ensure that top.qsf and top.qpf are not included "
                    "because those files are generated via the archiver, and we don't want to overwrite existing files")
                return False
    # If we do not find any "illegal" files, then the project is ready to be archived
    filelist.close()
    return True


# Original Command: #!/bin/csh -f   set dest = `echo *.par | sed 's/.par//'`;
# quartus_sh --archive -input filelist.txt -output $dest.qar
def qarchive(file_path=None, proj_name=None):
    """
    Archives the quartus project into a .qar file
    :param file_path: path/location of "top" design to archive
    :return: A Tuple of the command line result of the archive command, and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    if not proj_name:
        # Finds a .par so we know the name of the .qar to create
        proj_name, proj_found = get_proj_name()
        if not proj_found:
            logging.error(proj_name)
            return proj_name, False
        logging.debug("Found project name = " + proj_name + ".par")

    # Remove any existing .qar with the same project name
    if os.path.isfile(proj_name + ".qar"):
        logging.info("Already found a .qar with the same name as the project.  Removing to create a new one")
        os.remove(proj_name + ".qar")

    # This command archives the design using the quartus shell
    try:
        command = "quartus_sh --archive -input filelist.txt -output " + proj_name + ".qar"
        out = subprocess.check_output(command, shell=True)
        logging.debug(out)
        success = True
    except subprocess.CalledProcessError as test_except:
        # If we run into an issue archiving the design, log the error
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred archiving project: " + error_msg)
        success = False
        out = test_except.output
        logging.info(out)
    # Print useful messages
    if success:
        logging.info("Successfully archived a project and generated a .qar with the same name of the .par")
    else:
        logging.error("Error archiving project to a .qar")
    return out, success


# Original Command: #!/bin/csh -f   set dest = `echo *.par | sed 's/.par//'`;
# quartus_sh --archive -input filelist.txt -output $dest.qar
def qarchive_package(file_path=None):
    """
    Archives the quartus project into a .qar file
    :param file_path: path/location of "top" design to archive
    :return: A Tuple of the command line result of the archive command, and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Finds a .qpf so we know the name of the .qar to create
    proj_name, proj_found = get_qpf_name()
    if not proj_found:
        logging.error(proj_name)
        return proj_name, False
    logging.debug("Found project name = " + proj_name + ".qpf")

    # Remove any existing .qar with the same project name
    if os.path.isfile(proj_name + ".qar"):
        logging.info("Already found a .qar with the same name as the project.  Removing to create a new one")
        os.remove(proj_name + ".qar")

    # This command archives the design using the quartus shell
    try:
        command = "quartus_sh --archive -input filelist.txt -output " + proj_name + ".qar"
        out = subprocess.check_output(command, shell=True)
        logging.debug(out)
        success = True
    except subprocess.CalledProcessError as test_except:
        # If the quartus shell encounters an error when packaging the project, throw an error
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred archiving project to a .qar : " + error_msg)
        success = False
        out = test_except.output
        logging.info(out)
    # Print useful messages
    if success:
        logging.info("Successfully archived a project and generated a .qar with the same name of the .par")
    else:
        logging.error("Error archiving project to a .qar")
    return out, success


# Original Command: quartus_sh --flow compile top;
# if (-e output_files/top.sof) echo \"************ COMPILATION SUCCESSFUL! *************\"
def qcompile(file_path=None):
    """
    Compiles the design within the quartus shell
    :param file_path: path/location of "top" design to compile
    :return: A Tuple of the command line output of the compilation, and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Get rid of any output files that are already there to ensure the compilation completes successfully
    if os.path.isfile("output_files/top.sof"):
        logging.info("found an output file in output_files/top.sof; removing")
        os.remove("output_files/top.sof")

    # Execute the compilation via the quartus shell
    print('beginning compilation')
    try:
        cmd_output = subprocess.check_output("quartus_sh --flow compile top", shell=True)
        logging.debug(cmd_output)
        suc = True
    except subprocess.CalledProcessError as test_except:
        # If the quartus shell fails compilation, print out an error message to tell the user what is going on
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred compiling the project: " + error_msg)
        cmd_output = test_except.output
        logging.info(cmd_output)
        suc = False
    # Determines whether or not an output file was generated
    exists = os.path.isfile("output_files/top.sof")
    # Print a helpful message denoting the status of the compilation
    # If the compilation succeeded but an output file is not there, this is a strange case, so tell the user about it
    if suc and not exists:
        logging.error("The Quartus Shell says compilation was successful but there is no top.sof in the output_files "
                      "directory.")
        print ('successful compilation, no .sof')
    # If both an output file is there and the quartus shell compiled successfully, then we are good
    elif suc:
        logging.info("The Quartus Shell successfully compiled the project and generated an output file")
        print("quartus shell successfully compiled")
    # Otherwise, if no output file was generated and the compilation fails, say so and punt
    else:
        logging.error("The Quartus Shell encountered an error compiling the project.")
        print("compilation error")
		
    return cmd_output, exists


def list_all_files_in_directory(directory):
    """
    Returns a list of the files within the given directory
    :return: a list of all of the files in the directory
    """
    # Holds all of the files found in the directory
    file_list = []
    # Recursively get all of the files in the given directory
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            # Get the full pathname of the file, and add it to the list
            filepath = os.path.join(dirpath, filename)
            file_list.append(os.path.normpath(filepath))
    return file_list


def find_local_filepaths_of_type(file_ext):
    """
    Gets a list of all the local files of a certain type in a directory
    :param file_ext: a string representing the file type to search for
    :return: a list of paths to all of the files with the given type and their
    """
    # Make sure the file extension starts with a "."
    if file_ext[0] != ".":
        file_ext = "." + file_ext
    # Holds all of the files with the given extension
    file_list = []
    # Now get all of the files with the given extension
    for filename in os.listdir("."):
        # Skip over files that have .BAK in them because they will only confuse the compiler/archiver
        if filename.endswith(file_ext) and not filename.endswith(".BAK" + file_ext):
            file_list.append(filename)
    return file_list


def find_all_filepaths_of_type(file_ext):
    """
    Gets a list of all the files of a certain type in a directory
    :param file_ext: a string representing the file type to search for
    :return: a list of paths to all of the files with the given type and their
    """
    # Make sure the file extension has a dot before it
    if file_ext[0] != ".":
        file_ext = "." + file_ext
    # Holds all of the files with the given extension
    file_list = []
    # Now recursively get all of the files with the given extension
    for dirpath, dirnames, filenames in os.walk("."):
        # Do not include the test directory when searching for files
        if "test" in dirnames:
            dirnames.remove("test")
        for filename in filenames:
            # If any of the files have the given extension, add it to the list of files found
            if filename.endswith(file_ext):
                # Get the full pathname of the qar file and add it to the list of files
                filepath = os.path.join(dirpath, filename)
                file_list.append(os.path.normpath(filepath))
    return file_list

def find_specific_file(file_ext):
    """
    Gets a list of all the files of a certain type in a directory
    :param file_ext: a string representing the file type to search for
    :return: a list of paths to all of the files with the given type and their
    """
    # Holds all of the files with the given extension
    file_list = []
    # Now recursively get all of the files with the given extension
    for dirpath, dirnames, filenames in os.walk("."):
        # Do not include the test directory when searching for files
        if "test" in dirnames:
            dirnames.remove("test")
        for filename in filenames:
            # If any of the files have the given extension, add it to the list of files found
            if filename.endswith(file_ext):
                # Get the full pathname of the qar file and add it to the list of files
                filepath = os.path.join(dirpath, filename)
                file_list.append(os.path.normpath(filepath))
    return file_list
	
	
	
def string_of_all_filepaths_of_type(file_ext):
    """
    returns string of all basenames of specific file path types
    :param file_ext: a string representing the file type to search for
    :return: a list of paths to all of the files with the given type and their
    """
    strip_len = len(os.getcwd()) + 1
    # Make sure the file extension has a dot before it
    if file_ext[0] != ".":
        file_ext = "." + file_ext
    # Holds all of the files with the given extension
    file_list = ""
    # Now recursively get all of the files with the given extension
    for dirpath, dirnames, filenames in os.walk("."):
        # Do not include the test directory when searching for files
        if "test" in dirnames:
            dirnames.remove("test")
        for filename in filenames:
            # If any of the files have the given extension, add it to the list of files found
            if filename.endswith(file_ext) and not filename.endswith(".BAK" + file_ext):
                # Get the full pathname of the qar file and add it to the list of files
                #filepath = os.path.join(dirpath, filename)
                
                filepath = os.path.join(dirpath, filename)
                print(filepath)
                #filepath = filepath[strip_len:]
                file_list += filepath
                file_list += ' '                
    return file_list

	
def get_proj_name():
    """
    Gets the project name from the .par file
    :return: a string representing the name of the project, and True if it successfully found it
    """
    par_list = []
    # First look for any .par files in the cwd
    for filename in os.listdir("."):
        if filename.endswith(".par"):
            par_list.append(filename)
    # Find where the pesky .par file is in case it is buried in a subdirectory
    if len(par_list) == 0:
        logging.info("Could not find a .par in the current working directory.  Checking subdirectories for a .par")
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in filenames:
                if filename.endswith(".par"):
                    par_list.append(filename)
    # If there is only one PAR file, just return its name and we are done
    if len(par_list) == 1:
        return par_list[0][:-4], True
    # If we cannot find a .par file, throw an error and punt (there should be 1 in the directory)
    elif len(par_list) == 0:
        message = "Error: There is no .par file found within the project structure.  Make sure there is one " \
                  "there otherwise we do not have a name for the project"
        return message, False
    # If we find multiple .par files, throw an error and punt (there really should only be 1)
    else:
        message = "Error: Multiple .par files found within the project structure.  Make sure there is only " \
                  "one or if there are more than one, the desired project is the only one in the current " \
                  "working directory"
        return message, False


def get_qar_name():
    """
    Gets the project name from the .qar file
    :return: a string representing the name of the project, and True if it successfully found it
    """
    # Holds a list of all of the .qar files in the current directory
    qar_list = []
    # First look for any .qar files in the cwd
    for filename in os.listdir("."):
        if filename.endswith(".qar"):
            qar_list.append(filename)
    # If there is only one .qar file, just return its name and we are done
    if len(qar_list) == 1:
        return qar_list[0], True
    # If we cannot find a .qar file, throw an error and punt (there should be 1 in the directory)
    elif len(qar_list) == 0:
        message = "Error: There is no .qar file found within the project structure.  Make sure there is one there, " \
                  "otherwise we do not have a name for the project"
        return message, False
    # If we find multiple .qar files, throw an error and punt (there really should only be 1)
    else:
        message = "Error: Multiple .qar files found within the project structure.  Make sure there is only one or " \
                  "if there are more than one, the desired project is the only one in the current working directory"
        return message, False


def get_qpf_name():
    """
    Gets the project name from the .qpf file
    :return: a string representing the name of the project, and True if it successfully found it
    """
    par_list = []
    # First look for any .par files in the cwd
    for filename in os.listdir("."):
        if filename.endswith(".qpf"):
            par_list.append(filename)
    # Find where the pesky .par file is in case it is buried in a subdirectory
    if len(par_list) == 0:
        logging.info("Could not find a .qpf in the current working directory.  Checking subdirectories for a .par")
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in filenames:
                if filename.endswith(".qpf"):
                    par_list.append(filename)
    # If there is only one .qpf file, just return its name and we are done
    if len(par_list) == 1:
        return par_list[0][:-4], True
    # If we cannot find a .qpf file, throw an error and punt (there should be 1 in the directory)
    elif len(par_list) == 0:
        message = "Error: There is no .qpf file found within the project structure.  Make sure there is one there " \
                  "otherwise we do not have a name for the project"
        return message, False
    # If we find multiple .qpf files, throw an error and punt (there really should only be 1)
    else:
        message = "Error: Multiple .qpf files found within the project structure.  Make sure there is only one or if " \
                  "there are more than one, the desired project is the only one in the current working directory"
        return message, False


def simplify_path(path):
    """
    Given a path, simplifies it
    :param path: a path to the given file to simplify
    :return: a path with all of the crap removed
    """
    # If we don't have a path, punt
    if path is None:
        return
    # Split the path at each slash, as those are directories
    pathlist = path.split('/')
    res = []
    for x in pathlist:
        # Ignore double slashes
        if x == '':
            continue
        # Ignore periods, as they do not add anything to the path
        if x == '.':
            continue
        # If we encounter a previous directory command, remove the last thing from the queue
        if x == '..':
            if len(res) > 0:
                res.pop()
                continue
            # If we reach the end of the list, don't pop or we will get an index error
            else:
                continue
        # Add the current item to the path we are creating
        res.append(x)
    # If there is no path at all, just return a slash
    if len(res) == 0:
        return '/'
    # Create the path by adding slashes between the items
    res = [''] + res
    return '/'.join(res)


def remove_folder(path):
    """
    Removes the folder specified by path
    :param path: path to the folder to remove
    :return: True of successful
    """
    # Check if folder exists
    if os.path.exists(path):
        # Remove if exists, recursively getting rid of all the shit inside
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        # Then remove the overall folder
        os.rmdir(path)
    # Return true if the removal was successful
    return True


def fix_archive_errors(command_output):
    """
    If we get errors in qarchive, we can hopefully use this to fix them
    :param command_output: The output from the archive (with an error message hopefully)
    :return: True if the error was fixed
    """
    logging.info("Attempting to fix errors that occurred when attempting to archive the design to a .qar")
    fixed = False
    # See if any of the errors we encounter we can fix by scanning through the command line output
    while not fixed:
        # This part of the code fixes errors with missing files or files that were not archived
        if "Error: The following files were not archived" in command_output:
            logging.info("Error archiving design because of missing files.  Attempting to resolve file locations")
            success = fix_missing_files(command_output)
            # Re-archive the design if we find the missing file
            if success:
                logging.info("Successfully resolved all missing file errors")
                fixed = True
                break
        # If we get here, that means that no fixable errors were found, so we break and leave
        logging.error("Could not find a fixable error in the project :(  Check the command line output for "
                      "an error code")
        return False
    return fixed


def fix_missing_files(command_output):
    # First find all the files that are missing by searching through the command line output
    missing_files_list = find_missing_files(command_output)
    # Make sure we found at least one file within the project
    if not missing_files_list:
        logging.error("Could not find any missing files within the project")
        return False
    # Try to resolve each missing file issue by searching for it
    for full_path in missing_files_list:
        # First get the name and location of the file
        file_name = full_path.split("/")[-1]
        file_path = full_path.split(file_name)[0]
        # If our file path was blank, default it to the cwd
        if file_path == "":
            file_path = "."
        logging.debug("Looking for " + file_name + " within the project directory")
        # This holds all instances of the missing file found within the directory
        file_found = []
        # Now recursively look for the filename somewhere within the project directory
        for root, dirs, files in os.walk("."):
            # Ignore the test directory; we will definitely not find the file in there
            if "test" in dirs:
                dirs.remove("test")
            # If one of the files we find is one of the missing files, then add it to the files we have found
            for rec_file in files:
                if rec_file.endswith(file_name):
                    file_found.append(os.path.join(root, rec_file))
        # If we cannot find the file within the directory, try checking for a megawizard issue, otherwise we have to
        # punt
        if len(file_found) == 0:
            # Check if the missing file was because of a megawizard upgrade issue
            if file_name.endswith((".ppf", ".inc", ".cmp", ".bsf", "_inst.v", "_bb.v")):
                # Get rid of all of the illegal characters
                return upgrade_megawizard(file_name.split("_inst.v")[0].split("_bb.v")[0])
            logging.error("Searched for " + file_name + " within the project, but could not find it anywhere in the "
                                                        "project directory.  Make sure it is actually included, "
                                                        "or we cannot archive the design.  Alternatively, if the file "
                                                        "is not needed, remove it from the filelist.txt.")
            return False
        # If we find multiple files that match the name of our file, only add the first one we have found
        elif len(file_found) > 1:
            # If we want to restrict this to only one file, let is do so eventually
            logging.info("found multiple files with name " + file_name)
        # Make sure the files are not the same:
        if os.path.normpath(full_path) == os.path.normpath(file_found[0]):
            continue
        # Otherwise copy the files into the location specified
        logging.info("Found " + file_name + " in " + file_found[0] + ", copying to " + file_path)
        try:
            shutil.copyfile(file_found[0], full_path)
        # If we get an error copying the file, it is probably because the folders do not exist, so recursively create
        # them
        except IOError:
            logging.warning("Directory " + file_path + " does not exist.  Creating directory")
            # Makedirs recursively creates all needed directories
            os.makedirs(file_path)
            # Try copying the file again now that we have created the full path
            shutil.copyfile(file_found[0], full_path)

    # If we have found all of the missing files and copied them where expected, then we were successful
    return True


def find_missing_files(command_output):
    """
    This function finds all of the missing files and returns a list of them from the command line output.
    Used for finding the missing files
    :param command_output: Command Line output from qarchive
    :return: a list of all of the missing files
    """
    # Holds all of the files determined to be missing via the command line output
    missing_files = []
    # Missing files are the ones that show up indented after this line
    for line in command_output.split("Error: The following files were not archived\n")[1].splitlines():
        if line.startswith(" "):
            # Get the name of the missing file by removing whitespace and splitting at the error
            missing_files.append(line.split("Error: ")[1].strip())
        # Once we get to the indented lines, we have found all of the missing files, so return the missing files list
        else:
            break
    return missing_files


def upgrade_megawizard(file_name):
    """
    Performs an upgrade on the specified megawizard component based on a missing file
    :param file_name: the name of the file to update the megawizard file on
    :return: True if successful, False if not
    """
    # First get the name of the verilog file we wish to search for
    verilog_file = file_name.split(".")[0] + ".v"
    logging.info("Error in compilation because Megawizard files were not generated, searching for " + verilog_file +
                 " to regenerate the megawizard files on")
    # Now find the verilog file to perform the upgrade on
    verilog_file_path = None
    for root, dirs, files in os.walk("."):
        for each_file in files:
            # Once we find the path of the missing verilog file name, we are ready to upgrade the component
            if verilog_file in each_file:
                verilog_file_path = os.path.join(root, each_file)
    # If we do not find the specified verilog file name, then we cannot upgrade the Megawizard files
    if not verilog_file_path:
        logging.error("Megawizard update was unsuccessful; Could not find verilog file " + verilog_file)
        return False

    # Now execute the command to regenerate megawizard files
    logging.info("Upgrading Megawizard files for " + verilog_file_path)
    command = "qmegawiz -silent " + verilog_file_path
    # Try executing the command to upgrade the megawizard components
    try:
        cmd_output = subprocess.check_output(command, shell=True)
        success = True
        logging.debug(cmd_output)
    # If we run into an issue upgrading the megawizard files, print the error message
    except subprocess.CalledProcessError as test_except:
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred regenerating the megawizard files for " + verilog_file + error_msg)
        success = False
        cmd_output = test_except.output
        logging.error(cmd_output)
    # Print/log a helpful error message
    if success:
        logging.info("Successfully regenerated megawizard files for " + verilog_file)
        return True
    logging.error("An error occurred regenerating the megawizard files for " + verilog_file)
    return False


def fix_compile_errors(command_output):
    """
    If we get errors in qcompile, we can hopefully use this to fix them
    :param command_output: The output from the compilation (with an error message hopefully)
    :return: True if the error was fixed
    """
    # First assume we have not run into the issue
    fixed = False
    while not fixed:
        # Deal with error if IP components are out of date
        if "Error (11871):" in command_output:
            logging.info("Error in compilation because IP components are out of date; upgrading the IP components "
                         "(Error 11871).")
            cmd_output, success = upgrade_ip()
            # If the qshell is successful, then we can try recompiling the design
            if success:
                logging.info("Error 11871 fixed")
                fixed = True
                break
        # Deal with error if certain components are not added
        if "Error (12252):" in command_output:
            logging.info("Error in compilation because some IP was missing from the filelist.txt (Error 12252). "
                         " Adding it to the filelist")
            success = fix_missing_component(command_output.split("Error (12252):")[1])
            # If the qshell is successful, then we can try recompiling the design
            if success:
                logging.info("Error 112252 fixed")
                fixed = True
                break
        # Deal with error if a file is missing (non-IP I assume)
        if "Error (332000):" in command_output:
            logging.error("Error in compilation because of a missing file (Error 332000); looking for missing file")
            success = find_missing_non_ip(command_output.split("Error (332000): couldn't read file \"")[1], False)
            # If the qshell is successful, then we can try recompiling the design
            if success:
                logging.info("Error 332000 fixed")
                fixed = True
                break
        # Deal with error if other files are missing as well
        if "Error (12006):" in command_output:
            logging.error("Error in compilation because of a missing file (Error 12006); looking for missing file")
            success = find_missing_non_ip(command_output.split("instantiates undefined entity \"")[1], True)
            # If the qshell is successful, then we can try recompiling the design
            if success:
                logging.info("Error 12006 fixed")
                fixed = True
                break
        # Deal with error if a component is missing
        if "Error (12007):" in command_output:
            logging.error("Error in compilation because of a mismatch in Top-level entity (Error 12007); "
                          "looking for missing file")
            success = find_missing_non_ip(command_output.split("entity \"")[1], True)
            # If the qshell is successful, then we can try recompiling the design
            if success:
                logging.info("Error 12007 fixed")
                fixed = True
                break
        # If we get here, that means that we have not found a fixable error and we have to punt
        logging.error("Could not find a fixable error in the project :(  Check the command line output for "
                      "an error code")
        return False
    return fixed


def upgrade_ip(proj_name="top", file_path=None):
    """
    Upgrades the IP files using a shell command
    :param proj_name: optional name of project to perform IP upgrade on
    :param file_path: file_path: path/location of "top" design to compile
    :return: A tuple of the command line output of the compilation, and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # The command we wish to run on the quartus shell is as follows; upgrade ALL ip not just required ones
    command = "quartus_sh --ip_upgrade -mode all " + proj_name
    # Try executing the quartus shell command
    try:
        cmd_output = subprocess.check_output(command, shell=True)
        logging.debug(cmd_output)
        logging.info("IP Upgrade executed successfully")
        success = True
    # If we run into an issue upgrading the IP, print out the error code/message
    except subprocess.CalledProcessError as test_except:
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        cmd_output = test_except.output
        logging.info(cmd_output)
        logging.error("An error occurred when upgrading IP: " + error_msg)
        success = False
    # Spit out the command line result and whether the IP Upgrade was successful
    return cmd_output, success


def fix_missing_component(command_output):
    """
    This function adds any missing components to the filelist.txt so they are added to the directory
    :param command_output: Output of the compilation (with an error message we can parse hopefully)
    :return: True if files were added to the filelist.txt, False if not
    """
    # First try compiling the design to re-generate any files thaat could be missing
    logging.info("First trying compilation of original design to generate possible files")
    comp_cmd, compilation_good = qcompile()
    # If the compilation is not successful, then we have other issues to deal with besides missing files
    if not compilation_good:
        logging.error("Could not compile the original extracted design.  Likely an issue exists in the project")
        return False
    # Keeps track of the components that were deemed to be missing
    components = []
    # Determine which components are missing by parsing the commandline output and removing whitespace
    missing = command_output.split("Component")[1].split()[0].strip()
    logging.info("Searching for " + missing + " in file directory")
    # Now look for any file that has this name, which will hopefully be in the directory
    for root, dirs, files in os.walk("."):
        for each_file in files:
            # If we do find the missing file somewhere in the directory, then copy it into files we plan on writing to
            # the filelist.txt
            if missing in each_file:
                components.append(os.path.join(root, each_file))
    # If we do not find any components in the file structure that match the name, return an error and punt
    if not components:
        logging.error("Could not find any files matching " + missing + ". Make sure all required files are added "
                                                                       " to the filelist.txt!")
        return False
    # If we did find some components in the project directory, add it to the filelist.txt so they get archivved
    logging.info("Adding " + str(components) + " to filelist.txt")
    return write_files_to_filelist(components)


def find_missing_non_ip(command_output, search=False):
    """
    This function adds any missing components to the filelist.txt so they are added to the directory
    :param command_output: Output of the compilation (with an error message hopefully)
    :param search: Parameter deciding whether or not we should search for the missing module in the structure
    (i.e. not a direct filename)
    :return: True if missing file was added to filelist.txt, False if not
    """
    # First get the name of the missing file
    missing = command_output.split("\"")[0]
    # If we do not want to search for the file (i.e. the file path was explicitly given in the command), simply write it
    # to the filelist.txt
    if not search:
        missing_files = [missing]
    # Otherwise, we need to search for the given module by crawling through the .v files
    else:
        logging.info("Searching recursively in the project directory for a verilog file with module:  " + missing)
        # This function hopefully finds a verile file that contains the missing module
        missing_files = search_for_module(missing)
        # If we do not find any files that contain this module, then punt and return an error
        if not missing_files:
            return False
    logging.info("Trying to add " + str(missing_files) + " to filelist.txt, as it was found missing by the compiler")
    # If the file exists, all we need to do is add it to the filelist.txt
    return write_files_to_filelist(missing_files)


def find_files_that_contain(name):
    """
    Finds a list of all files that contain the given name
    :param name: The name to search for within the directory
    :return: A list containing all of the files found containing the given name
    """
    # The files we find that have the given name inside of them
    files_found = []
    # Not recursively look for files with "name" somewhere within the project directory
    for root, dirs, files in os.walk("."):
        # Ignore anything inside the test directory because the file will not be in there
        if "test" in dirs:
            dirs.remove("test")
        # For each file we do find, check to see if the wanted name is part of it
        for rec_file in files:
            # If we do find the wanted name as part of the filename, add it to the list of files we want to include
            if name in rec_file:
                files_found.append(os.path.join(root, rec_file))
    # If we don't find any matching files, then that sucks :(
    if len(files_found) == 0:
        # We did not successfully fix this error in this case
        logging.error("Tried to find files with a module named " + name + "within the project, but could not find it.  "
                                                                          "Please add the .v file containing this "
                                                                          "module to the filelist.txt so the archive "
                                                                          "can run ")
        return False
    # Otherwise return the list of all of the files
    return files_found


def search_for_module(module_name):
    """
    Returns a list of all of the files that have the module module_name
    :param module_name: the module to search for in all of the .v files
    :return: A list of all of the files
    """
    # Look for any line that starts with module and includes the missing module name
    module_definition = "module\s+" + module_name
    # Keep track of all of the files that contain this module declaration (there should only be one)
    files_found = []
    # Not recursively look for files containing "module_name" somewhere within the project directory
    for root, dirs, files in os.walk("."):
        # Do not look in the test directory; it won't be there anyways
        if "test" in dirs:
            dirs.remove("test")
        # Iterate through each file to search for the wanted module definition
        for rec_file in files:
            # Make sure the file is a .v and contains the wanted module
            if rec_file.endswith(".v"):
                file_path = os.path.join(root, rec_file)
                # Search for the module definition in the verilog file
                verilog_file = open(file_path, "r")
                for line in verilog_file:
                    # If we find the given modeule definition, then add the current .v file to the list of files to add
                    if re.search(module_definition, line):
                        files_found.append(file_path)
                        break
                # Close the file since we are done reading from it.
                verilog_file.close()
    # If we don't find any matching files, then that sucks :(
    if len(files_found) == 0:
        logging.error("Could not find a verilog file that includes " + module_name + " within the project")
        return False
    # Otherwise return the list of all of the files
    return files_found


def batch_migrate(file_path=None):
    """
    This function performs migrate on a series of files in a directory
    :param file_path: optional path/location to move to
    :return: True if all files were successful, False if not
    """
    split_line = "*******************************************************************************\n"
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # Setup logging
    logging_config('batch_migration_result.log')
    # First make the successful and failed directories:
    suc_dir = "migration_successful"
    if not os.path.exists(suc_dir):
        os.mkdir(suc_dir)
    fail_dir = "migration_failed"
    if not os.path.exists(fail_dir):
        os.mkdir(fail_dir)
    # Find all of the .par files in the cwd
    par_files = find_local_filepaths_of_type(".par")
    if not par_files:
        logging.error("No .par files in the current directory.  Make sure .par files are in the cwd or "
                      "change the directory to the one with the .par files")
        return False
    migrate_successful = []
    migrate_failed = []
    # Now perform the migrate on each of the .par files
    for par in par_files:
        par_name = par.split('.')[-2]
        # This line splits between each project in the log
        logging.info("\n" + split_line + split_line + split_line + "Beginning Migration of " + par_name +
                     ":\n" + split_line + split_line)
        remove_folder(par_name)
        # Make sure the directory doesn't already exist
        try:
            os.mkdir(par_name)
        except IOError:
            remove_folder(par_name)
            os.mkdir(par_name)

        shutil.move(par, par_name + "/" + par)
        # # Log directly to a file in the folder
        # logging.basicConfig(filename=par_name + "/migration.log", level=logging.INFO)
        # If the migration is successful, then move the project to the happy folder :)
        if migrate(None, par_name):
            logging.info("Quartus project " + par_name + " successfully migrated")
            os.chdir("..")
            migrate_successful.append(par)
            remove_folder(suc_dir + "/" + par_name)
            shutil.move(par_name, suc_dir)
        # If the migration failed, move it to the sad folder :(
        else:
            logging.error("Quartus project " + par_name + " encountered an error in migration")
            os.chdir("..")
            migrate_failed.append(par)
            remove_folder(fail_dir + "/" + par_name)
            shutil.move(par_name, fail_dir)
    # Now, if all of the files were successfully migrated, no need to keep the failed directory
    if len(par_files) == len(migrate_successful):
        logging.info("All .par files were migrated successfully")
        logging.info(".par files that succeeded migration are " + str(migrate_successful) + ".  You can find them "
                                                                                            "in the " + suc_dir +
                                                                                            " directory.")
        # Also remove the failed directory if nothing is inside (since all designs passed)
        if os.listdir(fail_dir) == "":
            remove_folder(fail_dir)
        return True
    # Otherwise, print out the ones that failed and succeeded, and print False
    logging.info(".par files that succeeded migration are " + str(migrate_successful) + ".  You can find them "
                                                                                        "in the " + suc_dir +
                                                                                        " directory.")
    logging.info(".par files that failed the migration are " + str(migrate_failed) + ".  You can find them in the " +
                 fail_dir + " directory.")
    return False


def remove_duplicates(lst):
    """
    This function removes duplicates from a list
    :param lst: input list to remove duplicates from
    :return: a new lst with the duplicates removed
    """
    print('Removing Duplicates')
    # Holds the "uniqified" list
    lst2 = []
    # Only add files that are not in the resulting list
    for item in lst:
        if item not in lst2:
            lst2.append(item)
    return lst2


def print_help():
    """
    Thus function prints help for the migration process
    :return: N/A
    """
    # Change directory to where the instructions are
    current_dir = os.getcwd()
    # Path to the help document
    os.chdir("/data/pmayer/Python/Test/unix_commands")
    instructions = open("instructions.txt", 'r')
    # Print each line of the help document out to the user
    for line in instructions.readlines():
        print line
    instructions.close()
    # Change directory back to where we were before
    os.chdir(current_dir)
    return

    # print 'This script helps with migrating projects to newer versions of quartus.  To use it, you will want ' \
    #       'to first enter the quartus shell of the version you want to migrate a project to.  Then call ' \
    #       '\'migrate_design().\' by using the following command: \n \n python -c \'from unix_qcommands import *;' \
    #       ' print migrate_design()\' \n \n You can optionally pass an argument to migrate which is a path to the ' \
    #       'location of the .par file which you wish to migrate. \n  You can also call batch_migrate(), which will ' \
    #       'perform the migrate process on a directory filled with .par files.  batch_migrate() takes the same ' \
    #       'optional argument as migrate_design(), and sorts the resulting files into a migration_succeeded or a ' \
    #       'migration_failed directory based on whether or not each design succeeded the migration process' \
    #       '\n \nThe other functionality of this script is the ability to archive designs.  Use the' \
    #       archive_design() function to perform a packaging of a quartus file, with an optional argument which is a
    #       path to the location of the project you wish to archive.'


def logging_config(file_name):

    """
    Archives the quartus project into a .qar file
    :param file_path: path/location of "top" design to archive
    :return: A Tuple of the command line result of the archive command, and True if no errors occurred
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)

    # Finds a .qpf so we know the name of the .qar to create
    proj_name, proj_found = get_qpf_name()
    if not proj_found:
        logging.error(proj_name)
        return proj_name, False
    logging.debug("Found project name = " + proj_name + ".qpf")

    # Remove any existing .qar with the same project name
    if os.path.isfile(proj_name + ".qar"):
        logging.info("Already found a .qar with the same name as the project.  Removing to create a new one")
        os.remove(proj_name + ".qar")

    # This command archives the design using the quartus shell
    try:
        command = "quartus_sh --archive -input filelist.txt -output " + proj_name + ".qar"
        out = subprocess.check_output(command, shell=True)
        logging.debug(out)
        success = True
    except subprocess.CalledProcessError as test_except:
        # If the quartus shell encounters an error when packaging the project, throw an error
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred archiving project to a .qar : " + error_msg)
        success = False
        out = test_except.output
        logging.info(out)
    # Print useful messages
    if success:
        logging.info("Successfully archived a project and generated a .qar with the same name of the .par")
    else:
        logging.error("Error archiving project to a .qar")
    return out, success	

def create_qar(qsf_name=None, file_path=None):
    """
    Internal nuts-and-bolts archive of a quartus project
    :param qsf_name: optional name of the .qsf file to use if there are multiple
    :param file_path: optional path/location to move to
    :return: True if no errors occurred and the project was archived successfully
    """
    # If no file path is given, no need to change directory
    if file_path:
        logging.debug("Changing directory to " + file_path)
        os.chdir(file_path)
    # First extract any existing .par that is already there
    cmd_output, suc = qrestore()
    if not suc:
        return False
    # Now generate files from qsys
    suc = qsys_gen()
    if not suc:
        return False
    # Now upgrade the ip cores for the project, fist by getting the name of the .qpf
    qpf_name, suc = get_qpf_name()
    if not suc:
        return False
    #cmd_output, suc = upgrade_ip(qpf_name)
    #if not suc:
     #   return False
    # First generate the platform_setup.tcl
    suc = q2p(qsf_name)
    if not suc:
        return False
    # Make sure if there are qip files, any qsys files referenced actually exist
    #suc = does_needed_qsys_exist()
    #if not suc:
    #    return False
    # Write all the files already in the filelist to a temporary location so we can write over the filelist.txt
    #suc = write_filelist_to_temp()
    #if not suc:
    #    return False
    # Now add all the IP from the platform_setup.tcl and .qip files
    suc = qsource()
    if not suc:
        return False
    # Do some cleaning of the filelist.txt
    update_filelist()
    f = open('filelist.txt', 'a')
    f.write('')
    f.close()
    # Now make sure nothing illegal has been added to the filelist.txt
    suc = ready_for_archive()
    if not suc:
        return False
    # Archive the project into a .qar file
    cmd_output, suc = qarchive_package()
    while not suc:
        if not fix_archive_errors(cmd_output):
            return False
        cmd_output, suc = qarchive_package()
    # Create a test directory to store the project and try expanding/compiling the design there
    suc = test_proj()
    if not suc:
        return False
    logging.info("-------------COMPILATION SUCCESSFUL HOORAY!!!!!!---------------")
    # Go up a directory to find the QAR name
    os.chdir("..")
    qar_name, found_qar = get_qar_name()
    # If we do not find a .qar in the current directory, throw an error
    if not found_qar:
        err_msg = "The design compiled successfully but could not find a .qar in the cwd.  " \
                  "Try looking in the project directory"
        logging.error(err_msg)
        return False
    # Give the location of the archived design
    archive_location = "****************************************************************\n The archived design can " \
                       "be found at " + qar_name + "\n****************************************************************"
    logging.info(archive_location)
    print archive_location

    return True	

def gen_ip_filelist():
    qsys_string = string_of_all_filepaths_of_type(".qsys")
    try:
        command1 = 'generate_ip_filelist.pl -qsys ' + qsys_string
        print (command1)
        out = subprocess.check_output(command1, shell=True)
        print('Gen IP filelist success: now archiving')
       
        success = True
        return out, success 
    except subprocess.CalledProcessError as test_except:
        # If the quartus shell encounters an error when packaging the project, throw an error
        error_msg = "error code: " + str(test_except.returncode) + "\n Output" + test_except.output
        logging.error("An error occurred archiving project to a .qar : " + error_msg)
        success = False
        out = test_except.output
        logging.info(out)
    return out, success
	


def cleanup_main (start_dir=None):
	
	print(color.BOLD+ color.PURPLE +'\nStarting Script\n' + color.END)
	if start_dir == None:
		cwd = os.getcwd()
	else:
		cwd = start_dir
	print(cwd)
	
	
	text = text_files(cwd)

	full_update_process(cwd, text)
	

def main (argv):
	#os.chdir('/data/jbosset/NUE/test_folder/A10_LCD_Tutorial')
	#good_test_rev1.create_qar()
	
	option_parser = optparse.OptionParser()

	option_parser.set_defaults(full_pack=False, qsys_check=False, output_files = False, build_filelist = None, 
		upgrade = None)

	# # Will upgrade every item in a subdirectory of the listed folder
	option_parser.add_option("-f", "--multiple_upgrade", action="store", dest="full_pack", default= None,
		help="runs full upgrade on all project files in directory")
	
	# #will list qsys and qip files in specified directory
	option_parser.add_option("-q", "--qsys_check", action="store_true", dest="qsys_check",
		help="Checks locations of qsys files in par; then lists QIP paths present")

	# #will check if output files is specified; if not it will add them
	option_parser.add_option("-o", "--output_files", action="store_true", dest="output_files",
		help="adds output files line to qsf")

	# #allows user to specify a software folder to be added to filelist; code automatically check for "software" folder but
		##this can add folder of another name... use only for build_filelist function
	option_parser.add_option("-s", "--sw_filelist", action="store", dest = "sw_filelist", default=None,
		help="adds sw to filelist.txt")
		
	# #is directory specifier; needed for output files function and for build_filelist function
	option_parser.add_option("-d", "--directory", dest="start_directory", action="store", default= None,
		help= "Specifies directory to operate; use in conjunction with other function")


	# #will build filelist for project 
	option_parser.add_option("-c", "--create_qar", dest="build_filelist", action="store",
		help= "Will build project archive (.par)")
		
	# #new .qar's will need a name. use this to specify qar name. must be used in conjunction with build_filelist
	option_parser.add_option("-n", "--name", dest="proj_name", action="store", default = None,
		help= "Specifies project name for .par (is needed for packaging a new project; not needed for update)")
	
	
	option_parser.add_option("-u", "--single_upgrade", dest="upgrade", action="store",
		help="Will upgrade qsys based IP")	
		
	options, args = option_parser.parse_args(argv)
	
	if options.upgrade != None:
		os.chdir(options.upgrade)
		single_update_process(main_dir = options.upgrade)
	
	if options.full_pack != None:
		print("full_pack is TRUE")
		cleanup_main(start_dir = options.full_pack)
	if options.qsys_check == True:
		if options.start_directory != 'NO_DIR':
			qsys_checker(main_dir= options.start_directory)
	if options.output_files == True:
		if options.start_directory != 'NO_DIR':
			output_file_path(main_dir= options.start_directory)			
		else:
			print('no directory; please use --directory to establish a path')
	if options.sw_filelist and options.build_filelist != None:
		add_SW_to_IP_filelist(main_dir=options.start_directory, sw_folder = options.sw_filelist)
	if options.build_filelist != None:
		build_filelist(main_dir=options.build_filelist, sw_folder = options.sw_filelist, proj_name = options.proj_name,file_path=options.start_directory)
		
		

		
if __name__ == '__main__':
	running = main(sys.argv)
	sys.exit(running)
