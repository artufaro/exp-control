#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <getopt.h>
#include <errno.h>
#include <usb.h>
#include <libxml/xmlversion.h>
#include <libxml/xmlreader.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <gmp.h>

//ID
#define VASCO_USB_VID 0xa5a5
#define AD9958_PID    0x9958
#define AD9959_PID    0x9959

//usb commands
#define RESET_DDS          0x10
#define WRITE_IMMED        0x20
#define WRITE_IDX          0x30
#define ERASE_TABLE        0x40
#define WRITE_BLOCK        0x50
#define READ_BLOCK         0x60
#define WRITE_FCLOCK       0x70
#define READ_FCLOCK        0x80

#define USB_TMO            1000
#define RESETVAL              0
#define FNAMELEN            100

#define ACT_WRITE             1
#define ACT_READ              2
#define ACT_VERIFY            3
#define ACT_ERASE             4
#define ACT_SETCLK            5
#define ACT_GETCLK            6
 
//state byte
#define SETAMP     0x80
#define SETPH      0x40
#define SETFR      0x20
#define SETPD      0x10
#define SETAMPOFF  0x08

int ddstype=0,filetype=0;
int nch=0,tsize=0;
char *chs[4]={"ch0","ch1","ch2","ch3"};
mpf_t ddsfreq;

typedef struct {
  unsigned char a[2];
  unsigned char p[2];
  unsigned char f[4];
} chan_t;

typedef struct {
  chan_t ch[4];
} dds_t;

void reg2freq(mpf_t acc, unsigned char *f)
{
  unsigned aux;
  int i;
  
  aux=0;
  for(i=0;i<4;i++)
    {
      aux<<=8;
      aux+=f[i];
    }

  mpf_set_ui(acc,aux);
  mpf_mul(acc,acc,ddsfreq);
  mpf_div_2exp(acc,acc,32);
}

void freq2reg(const char *fs,unsigned char *f)
{
  int i;
  unsigned aux;
  mpf_t hf,freq;

  mpf_init_set_str(freq,fs,10);
  mpf_init_set_d(hf,0.5);

  mpf_mul_2exp(freq,freq,32);
  mpf_div(freq,freq,ddsfreq);
  mpf_add(freq,freq,hf);
  mpf_clear(hf);

  aux=mpf_get_ui(freq);
  mpf_clear(freq);

  for(i=3;i>=0;i--)
    {
      f[i]=aux;
      aux>>=8;
    }
}

void parsechan(xmlNodePtr np1,dds_t *dds,int i)
{
  xmlNodePtr np2;
  const xmlChar *name, *aux;
  unsigned ui;
  
  for(np2=np1->children;np2;np2=np2->next)
    {
      //freq
      if(!strncmp(np2->name,"fr",2))
	{
	  aux=xmlNodeGetContent(np2);
	  if(aux)
	    {
	      dds->ch[i].a[0]|=SETFR;
	      freq2reg(aux,dds->ch[i].f);
	      xmlFree(BAD_CAST aux);
	    }
	  continue;
	}
      //amp
      if(!strncmp(np2->name,"am",2))
	{
	  aux=xmlNodeGetContent(np2);
	  if(aux)
	    {
	      ui=strtol(aux,NULL,0);
	      xmlFree(BAD_CAST aux);
	      if(ui)
		{
		  if(ui<1024)
		    {
		      dds->ch[i].a[0]|=SETAMP;
		      dds->ch[i].a[1]|=ui;
		      dds->ch[i].a[0]|=(ui>>8) & 0x07;
		    }
		  else
		    dds->ch[i].a[0]|=SETAMPOFF;
		}
	      else
		dds->ch[i].a[0]|=SETPD;
	    }
	  continue;
	}
      //phase
      if(!strncmp(np2->name,"ph",2))
	{
	  aux=xmlNodeGetContent(np2);
	  if(aux)
	    {
	      dds->ch[i].a[0]|=SETPH;
	      ui=strtol(aux,NULL,0);
	      xmlFree(BAD_CAST aux);
	      dds->ch[i].p[1]=ui;
	      dds->ch[i].p[0]=ui>>8;
	    }
	  continue;
	}
    }
}

void readfile(char *fname,dds_t *dds)
{

  xmlTextReaderPtr reader;
  const xmlChar *name, *aux;
  xmlNodePtr np1,np2;
  int ret,idx,idxt,i;
  dds_t ddstmp;
  mpf_t freq;
  int amp;
  char *aux2; 
  char state;
  

  reader=xmlReaderForFile(fname,NULL,0);
  if(reader)
    {
      ret=xmlTextReaderRead(reader);
      if(ret==1)
	{
	  name=xmlTextReaderName(reader);
	  if(strncmp(name,"ad9958s",6) && strncmp(name,"ad9959s",6))
	    {
	      fprintf(stderr, "Wrong xml file name=%s\n",name);
	      xmlFree(BAD_CAST name);
	      xmlFreeTextReader(reader);
	      return;
	    }
	  filetype=strncmp(name,"ad9958s",6) ? AD9959_PID : AD9958_PID;
	  if(filetype!=ddstype)
	    {
	      fprintf(stderr, "File type and dds type mismatch\n");
	      xmlFree(BAD_CAST name);
	      xmlFreeTextReader(reader);
	      return;
	    }
	}

      ret=xmlTextReaderRead(reader);
      while(ret==1)
	{
	  name=xmlTextReaderName(reader);
	  if(!strncmp(name,"elem",4))
	    {
	      memset(&ddstmp,0,sizeof(dds_t));
	      idx=-1;
	      np1=xmlTextReaderExpand(reader);
	      for(np2=np1->children;np2;np2=np2->next)
		{
		  //index
		  if(np2->type==XML_TEXT_NODE)
		    {
		      idxt=strtol(np2->content,&aux2,0);
		      if((char *)np2->content != aux2)
			idx=idxt;
		    }
		  //ch
		  for(i=0;i<nch;i++)
		    {
		      if(!strncmp(np2->name,chs[i],3))
			{
			  parsechan(np2,&ddstmp,i);
			  break;
			}
		    }
		}
	      if(idx>=0 && idx<tsize)
		memcpy(dds+idx,&ddstmp,sizeof(dds_t));
	    }
	  ret=xmlTextReaderRead(reader);
	}
  
      xmlFreeTextReader(reader);

      if(ret!=0) 
	fprintf(stderr, "Failed to parse %s\n", fname);
    }
  else
    fprintf(stderr,"Unable to open %s\n", fname);
}

void writechan(xmlNodePtr np,dds_t *dds,int i)
{
  int k;
  mpf_t acc;
  char aux[20];
  unsigned ui;

  k=dds->ch[i].a[0];
  //freq
  if(k & SETFR)
    {
      mpf_init(acc);
      reg2freq(acc,dds->ch[i].f);
      gmp_snprintf(aux,20,"%8.3Ff",acc);
      xmlNewChild(np,NULL,BAD_CAST"fr",BAD_CAST aux);
      mpf_clear(acc);
    }
  //amp
  if(k & (SETAMP | SETPD | SETAMPOFF))
    {
      if(k & SETAMP)
	ui=((int)(k & 0x03)<<8)+dds->ch[i].a[1];
      if(k & SETPD)
	ui=0;
      if(k & SETAMPOFF)
	ui=1024;
      snprintf(aux,20,"%u",ui);
      xmlNewChild(np,NULL,BAD_CAST"am",BAD_CAST aux);
    }
  if(k & SETPH)
    {
      ui=((int)dds->ch[i].p[0]<<8)+dds->ch[i].p[1];
      snprintf(aux,20,"%u",ui);
      xmlNewChild(np,NULL,BAD_CAST"ph",BAD_CAST aux);
    }
}

void writefile(char *fname,dds_t *dds)
{
  int i,j,k;
  xmlDocPtr doc=NULL;
  xmlNodePtr root=NULL,np1,np2;
  char *rn;
  char aux[10];
  dds_t *dp;

  rn=(ddstype==AD9958_PID) ? "ad9958s" : "ad9959s";

  doc=xmlNewDoc(BAD_CAST"1.0");
  root=xmlNewNode(NULL,BAD_CAST rn);
  xmlDocSetRootElement(doc,root);
  
  for(i=0,dp=dds;i<tsize;i++,dp++)
    {
      k=0;
      for(j=0;j<nch;j++)
	k|=(dp->ch[j].a[0] & 0xf8);
      if(k)
	{
	  snprintf(aux,10," %d\n",i);
	  np1=xmlNewChild(root,NULL,BAD_CAST"elem",BAD_CAST aux);
	  for(j=0;j<nch;j++)
	    if(dp->ch[j].a[0] & 0xf8)
	      {
		np2=xmlNewChild(np1,NULL,BAD_CAST chs[j],BAD_CAST 0);
		writechan(np2,dp,j);
	      }
	}
    }
  xmlSaveFormatFileEnc(fname,doc,"ISO-8859-1",1);
  xmlFreeDoc(doc);
  xmlCleanupParser();
  
}

void readfclock(usb_dev_handle *hdev)
{
  unsigned char cmd, f[32];
  int n;
  
  cmd=READ_FCLOCK;
  usb_bulk_write(hdev,1,&cmd,1,USB_TMO);
  usb_bulk_read(hdev,2,f,32,USB_TMO);

  mpf_init_set_str(ddsfreq,f,10);

}

int writefclock(usb_dev_handle *hdev)
{
  unsigned char cmd[33];
  char aux[32];
  int i;
  
  memset(cmd,'\0',33);

  cmd[0]=WRITE_FCLOCK;
  i=gmp_snprintf(aux,32,"%8.3Ff",ddsfreq);
  strncpy(cmd+1,aux,i);

  sleep(1);
  i=usb_bulk_write(hdev,1,cmd,32,USB_TMO);
  sleep(1);

  return i; 
}

int erase(usb_dev_handle *hdev)
{
  char cmd;

  cmd=ERASE_TABLE;
  return usb_bulk_write(hdev,1,&cmd,1,USB_TMO);
}

int main(int argc, char**argv)
{    
  int found=0,i,err;
  unsigned char cmd[64];
  struct usb_device *dev;    
  struct usb_bus *bus=NULL;
  usb_dev_handle *hdev=NULL;
  FILE *fp;
  dds_t *dds;
  char c,*fname=NULL;
  int act=0;

      c=getopt(argc,argv,"w:r:v:s:geh?");
	printf("%c \n", c);

    /*  if (c==-1)
	if(act)
	  break;
	else
	  c='h';*/
      switch(c)
	{
	case 'w':
	  fname=strndup(optarg,FNAMELEN);
	  act=ACT_WRITE;
	  break;
	case 'r':
	  fname=strndup(optarg,FNAMELEN);
	  act=ACT_READ;
	  break;
	case 'v':
	  fname=strndup(optarg,FNAMELEN);
	  act=ACT_VERIFY;
	  break;
	case 's':
	  mpf_init_set_str(ddsfreq,optarg,10);
	  act=ACT_SETCLK;
	  break;
	case 'g':
	  act=ACT_GETCLK;
	  break;
	case 'e':
	  act=ACT_ERASE;
	  break;
	case 'h':
	case '?':
	default:
	  {
	    fprintf(stderr,"Usage: writetable -o -p -t -i -o -n -s \n");
	    fprintf(stderr,"       where valid options are: \n");
	    fprintf(stderr,"       -w fname :write table from file fname\n");
	    fprintf(stderr,"       -v fname :verify table from file fname\n");
	    fprintf(stderr,"       -r fname :read table to file fname\n");
	    fprintf(stderr,"       -e       :erase table\n");
	    fprintf(stderr,"       -s value :set clock freq. (Hz)\n");	    
	    fprintf(stderr,"       -g       :get clock freq. (Hz)\n");
	    fprintf(stderr,"       -h -?    :print this message\n");
	    exit(1);
	  }
	}

//  LIBXML_TEST_VERS

  usb_init();
  usb_find_busses();
  usb_find_devices();
  
  for(bus=usb_get_busses();bus;bus=bus->next) 
    {
      for(dev=bus->devices;dev;dev=dev->next) 
	{
	  if ((dev->descriptor.idVendor==VASCO_USB_VID) &&
	      ((dev->descriptor.idProduct==AD9958_PID) ||
	       (dev->descriptor.idProduct==AD9959_PID))) 
	    {
	      ddstype=dev->descriptor.idProduct;
	      found=1;
	      break;
	    }
	}
      if(found)
	break;
    }

  if(!found)
    {
      fprintf(stderr,"AD995X board not found\n");
      exit(1);
    }
  else
    {
      nch=(ddstype==AD9958_PID) ? 2 : 4;
      tsize=(ddstype==AD9958_PID) ? 1024 : 512;
    }

  dds=(dds_t *)calloc(tsize,sizeof(dds_t));
  if(!dds)
    {
      fprintf(stderr,"Error: cannot allocate memory\n");
      fclose(fp);
      exit(1);
    }

  hdev=usb_open(dev);
  if(!hdev) 
    {
      fprintf(stderr,"Can't open device\n");
      exit(1);	   
    }

  if(err=usb_set_configuration(hdev,3))
    {
	printf("error %d\n", err);
      fprintf(stderr,"Can't set configuration\n");
      exit(1);	   
    }

  if(usb_claim_interface(hdev,0))
    {
      fprintf(stderr,"Can't claim interface\n");
      exit(1);	   
    }


  if(act==ACT_WRITE || act==ACT_VERIFY)
    {
      readfclock(hdev);
      readfile(fname,dds);
    }

  switch(act)
    {
    case ACT_WRITE:
      if(erase(hdev)<0)
	{
	  fprintf(stderr,"Bulk write failed with code=%d\n",err);
	  break;
	}

      if(ddstype==AD9958_PID)
	for(i=0;i<tsize;i+=2)
	  {
	    cmd[0]=WRITE_BLOCK;
	    cmd[1]=i>>8;
	    cmd[2]=i & 0xff;
	    memcpy(cmd+3,dds+i,2*sizeof(chan_t));
	    memcpy(cmd+3+2*sizeof(chan_t),dds+i+1,2*sizeof(chan_t));
	    err=usb_bulk_write(hdev,1,cmd,4*sizeof(chan_t)+3,USB_TMO);
	    if(err<0)
	      {
		fprintf(stderr,"Bulk write failed with code=%d\n",err);
		fprintf(stderr,"at index %d\n",i);
		break;
	      }
	  }
      else
	for(i=0;i<tsize;i++)
	  {
	    cmd[0]=WRITE_BLOCK;
	    cmd[1]=i>>8;
	    cmd[2]=i & 0xff;
	    memcpy(cmd+3,dds+i,4*sizeof(chan_t));
	    err=usb_bulk_write(hdev,1,cmd,4*sizeof(chan_t)+3,USB_TMO);
	    if(err<0)
	      {
		fprintf(stderr,"Bulk write failed with code=%d\n",err);
		fprintf(stderr,"at index %d\n",i);
		break;
	      }
	  }  
      
    case ACT_VERIFY:
      for(i=0;i<tsize;i++)
	{
	  cmd[0]=READ_BLOCK;
	  cmd[1]=i>>8;
	  cmd[2]=i & 0xff;
	  err=usb_bulk_write(hdev,1,cmd,3,USB_TMO);
	  if(err<0)
	    {
	      fprintf(stderr,"Bulk write failed with code=%d\n",err);
	      break;
	    }
	  err=usb_bulk_read(hdev,2,cmd,nch*sizeof(chan_t),USB_TMO);
	  if(err<0)
	    {
	      fprintf(stderr,"Bulk read failed with code=%d\n",err);
	      fprintf(stderr,"at block %d\n",i);
	      break;
	    }
	  if(!cmd[0])
	    continue;
	  if(memcmp((const void*)cmd,(const void *)(dds+i),nch*sizeof(chan_t)))
	    fprintf(stderr,"Verify failed at index %d\n",i);
	}
      break;

    case ACT_READ:
      for(i=0;i<tsize;i++)
	{
	  cmd[0]=READ_BLOCK;
	  cmd[1]=i>>8;
	  cmd[2]=i & 0xff;
	  err=usb_bulk_write(hdev,1,cmd,3,USB_TMO);
	  if(err<0)
	    {
	      fprintf(stderr,"Bulk write failed with code=%d\n",err);
	      break;
	    }
	  err=usb_bulk_read(hdev,2,cmd,nch*sizeof(chan_t),USB_TMO);
	  if(err<0)
	    {
	      fprintf(stderr,"Bulk read failed with code=%d\n",err);
	      fprintf(stderr,"at block=%d\n",i);
	      break;
	    }
	  memcpy(dds+i,cmd,nch*sizeof(chan_t));
	}
      readfclock(hdev);
      writefile(fname,dds);
      break;

    case ACT_SETCLK:
      err=writefclock(hdev);
      if(err<0)
	fprintf(stderr,"Writefclock failed with code=%d\n",err);
      break;

    case ACT_GETCLK:
      readfclock(hdev);
      gmp_fprintf(stderr,"DDS Master clock=%8.3Ff Hz\n",ddsfreq);
      break;

    case ACT_ERASE:
      if(erase(hdev)<0)
	fprintf(stderr,"Erase failed with code=%d\n",err);
      break;
    }

  usb_release_interface(hdev,0);
  usb_close(hdev);
  free(dds);
  mpf_clear(ddsfreq);
  
  return 0;
}
