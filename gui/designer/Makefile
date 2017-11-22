###### EDIT ##################### 
#Directory with ui and resource files
RESOURCE_DIR = .
 
#Directory for compiled resources
COMPILED_DIR = ../ui
COMPILED_RESOURCES_DIR = ..
 
#UI files to compile
UI_FILES = $(wildcard $(RESOURCE_DIR)/*.ui)
#UI_FILES = mainwindow.ui
#Qt resource files to compile
RESOURCES = $(wildcard $(RESOURCE_DIR)/*.qrc)

#pyuic4 and pyrcc4 binaries
PYUIC = pyside-uic #pyuic4
PYRCC = pyside-rcc #pyrcc4
 
#################################
# DO NOT EDIT FOLLOWING
 
COMPILED_UI = $(UI_FILES:$(RESOURCE_DIR)/%.ui=$(COMPILED_DIR)/%_ui.py)
COMPILED_RESOURCES = $(RESOURCES:$(RESOURCE_DIR)/%.qrc=$(COMPILED_RESOURCES_DIR)/%_rc.py)
 
all : ui resources
 
resources : $(COMPILED_RESOURCES) 
 
ui : $(COMPILED_UI)
 
$(COMPILED_DIR)/%_ui.py : $(RESOURCE_DIR)/%.ui
	$(PYUIC) $< --from-imports -o $@
 
$(COMPILED_RESOURCES_DIR)/%_rc.py : $(RESOURCE_DIR)/%.qrc
	$(PYRCC) $< -o $@
 
clean : 
	$(RM) $(COMPILED_UI) $(COMPILED_RESOURCES) $(COMPILED_UI:.py=.pyc) $(COMPILED_RESOURCES:.py=.pyc)  
