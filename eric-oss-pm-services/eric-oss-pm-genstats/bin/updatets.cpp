// To compile gcc -o updatets updatets.cpp -lstdc++

// $Id: updatets.cpp 92 2012-02-22 13:38:34Z eeicmuy $

// ntohs, etc.
#include <arpa/inet.h> 
#include <string.h> 

#include <unistd.h>
#include <stdlib.h>

#include <iostream>
#include <fstream>

static const char *svn_id = "$Id: updatets.cpp 92 2012-02-22 13:38:34Z eeicmuy $"; 

using namespace std;

int debug = 0;

const unsigned char IN_EOF = -1;
const unsigned char IN_FAIL = -2;

const unsigned int REC_EVENT = 4;
const unsigned int REC_FOOTER = 7;

const unsigned int REC_MAX = 8;

struct recHeader {
  unsigned short length;
  unsigned char  type;
} __attribute__((__packed__));

struct GpehFooter {
  unsigned short year;
  unsigned char  month;
  unsigned char  day;
  unsigned char  hour;
  unsigned char  min;
  unsigned char  sec;
} __attribute__((__packed__));

unsigned char readRec( ifstream& in, struct recHeader* header, unsigned char** buff, unsigned int* buffSize ) {

  in.read( (char *)header, sizeof(recHeader) );
  if ( in.fail() ) {
    return IN_EOF;
  }

  unsigned short recLength = ntohs(header->length);
  unsigned char recType = header->type;
  if ( debug > 9 ) cout << "readRec: recLength=" << recLength << ", recType=" << (unsigned int)recType << endl;
  if ( recType > REC_MAX ) {
    cerr << "readRec: Invalid record type " << (unsigned int)recType << endl;
    return IN_FAIL;
  }

  int recDataLength = recLength - sizeof(recHeader);
  // Make sure the buff is large enough to hold the record
  if ( recDataLength >  *buffSize ) {
    if ( debug > 9 ) cout << "readRec: resizing buff from " << *buffSize << " to " << recDataLength << endl;
    if ( *buffSize > 0 )
      delete *buff;
    *buff = new unsigned char[recDataLength];
    *buffSize = recDataLength;
  }
	
  in.read ((char*)*buff, recDataLength);
  if ( in.fail() ) {
    cerr << "readRec: Failed to read record sized " << recDataLength << endl;
    return IN_FAIL;
  }

  return recType;
}

int writeRec( ostream* outRef, struct recHeader* header, unsigned char* buff ) {  
  unsigned int recLength = ntohs(header->length);
  if ( debug > 9 ) cout << "writeRec recLength=" << recLength << endl;

  outRef->write( (char *)header, sizeof(recHeader) );
  outRef->write( (char *)buff, recLength - sizeof(recHeader) );

  return recLength;
}

void processGpehEvent( unsigned char* buffer, struct tm* timeBase, unsigned int offset,
		       unsigned int fmtVer ) {

  unsigned int min = timeBase->tm_min + (offset / 60000);
  unsigned int sec = int ( (offset % 60000) / 1000);
  unsigned int msec = offset % 1000;
  
  // For P6.1.4 (FMT = 7-0) scannerid was inserted in as 
  // the first 24 bits of the event record header
  unsigned int hourByteIndex = 0;	  
  if ( fmtVer >= 70 ) {
    hourByteIndex = 3;
  }
  if ( debug > 7 ) { 
    cout << "processGpehEvent: hour=" << timeBase->tm_hour << ", min=" << min << ", sec=" << sec 
	 << ", msec=" << msec << ", hourByteIndex=" 
	 << hourByteIndex << endl; 
  }
  buffer[hourByteIndex + 0] = ( (timeBase->tm_hour & 0x1F) << 3 ) | ( (min & 0x3F) >> 3 );
  buffer[hourByteIndex + 1] = ( (min & 0x07) << 5) |  ( (sec & 0x3F) >> 1 );
  buffer[hourByteIndex + 2] = ( (sec & 0x1) << 7 ) | ( (msec & 0x07FF) >> 4 );
  buffer[hourByteIndex + 3] = ( (msec & 0xF) << 4 ) | (buffer[hourByteIndex + 3] & 0x0F);

  if ( debug > 7 ) {
    cout << "processGpehEvent: " << hex 
	 << (unsigned short)buffer[hourByteIndex + 0] << " "
	 << (unsigned short)buffer[hourByteIndex + 1] << " "
	 << (unsigned short)buffer[hourByteIndex + 2] << " "
	 << (unsigned short)buffer[hourByteIndex + 3] 
	 << dec << endl;
  }

}

void updateTimeStamps( ifstream& in, ostream* outRef, struct tm* timeBase,
		       unsigned int step, unsigned int fmtVer ) {
  unsigned int offset = 0;
  
  struct recHeader header;
  unsigned char* buffer;
  unsigned int buffSize = 0;
  
  unsigned int bytesRead = 0;
  unsigned int recRead = 0;
  unsigned int recWrite = 0;
  unsigned char recType = 0;

  while ( (recType = readRec( in, &header, &buffer, &buffSize )) != IN_EOF && recType != IN_FAIL ) {
    bytesRead += ntohs(header.length);
    recRead++;
    
    if ( recType == REC_EVENT ) {
      processGpehEvent( buffer, timeBase , offset, fmtVer );
      writeRec( outRef, &header, buffer );
      
      recWrite++;
      offset += step;
    }
    
    if ( debug > 9 ) 
      cout 
	<< "bytesRead=" << bytesRead 
	<< ", recRead=" << recRead 
	<< ", recWrite=" << recWrite
	<< endl;
  }
 
  if ( buffSize > 0 ) {
    delete buffer;
  }

  if ( recType == IN_FAIL ) {
    cerr << "Failed to read record " << (recRead + 1) << " at byte " << bytesRead << endl;
    exit(1);
  }

}

void randomize( unsigned char* buff, unsigned int offset, unsigned int buffSize, int randomBytes ) {
  unsigned int byteIndex = buffSize;
  unsigned int rBytesLeft = 0;
  unsigned int randomData;
  while ( byteIndex >= offset && ((buffSize - byteIndex) < randomBytes) ) {
    if ( rBytesLeft == 0 ) {
      randomData = random();
      rBytesLeft = 4;
    }

    unsigned char rByte = (unsigned char)(randomData && 0xFF);
    randomData >> 8;
    rBytesLeft--;

    buff[byteIndex] = rByte;
    byteIndex--;
  }
}

void updateScannerId( unsigned char* buff, unsigned int scannerID ) {
  buff[0] = (unsigned char)((scannerID >> 16) & 0xFF);
  buff[1] = (unsigned char)((scannerID >>  8) & 0xFF);
  buff[2] = (unsigned char)((scannerID >>  0) & 0xFF);
}

void makeFile( ifstream& in, ostream* outRef, 
	       unsigned int targetSize, unsigned int fmtVer, 
	       unsigned int randomBytes, unsigned int scannerID ) {
  unsigned char* buff;
  unsigned int buffSize = 0;
  struct recHeader header;

  unsigned int offSet = 5;
  if ( fmtVer >= 70 )
    offSet += 3;

  unsigned int bytesRead = 0;
  unsigned int bytesWritten = 0;
  unsigned int recRead = 0;
  unsigned int recWrite = 0;
  
  unsigned int passCount = 1;
    
  while ( bytesWritten < targetSize ) {
    if ( in.eof() ) {
      passCount++;
      in.clear();
      in.seekg(0, ios::beg);
    }

    cout << "Starting pass " << passCount << endl;

    while ( ! in.eof() && (bytesWritten < targetSize) ) {
      unsigned char recType = readRec( in, &header, &buff, &buffSize );
      if ( recType != IN_EOF ) {
	bytesRead += ntohs(header.length);
	recRead++;
	
	if ( recType == REC_EVENT ) {
	  if ( randomBytes > 0 ) {
	    unsigned int recLength = ntohs(header.length) - sizeof(recHeader);
	    randomize( buff, offSet, recLength, randomBytes );
	  }
	  
	  if ( fmtVer >= 70 && scannerID > 0 ) 
	    updateScannerId( buff, scannerID );
	  
	  bytesWritten += writeRec( outRef, &header, buff );
	  recWrite++;
	}

	if ( debug > 9 ) 
	  cout 
	    << "makeFile: bytesRead=" << bytesRead 
	    << ", recRead=" << recRead 
	    << ", recWrite=" << recWrite
	    << ", bytesWritten=" << bytesWritten
	    << endl;
      }
    }
  }

  if ( buffSize > 0 ) 
    delete buff;
  
  cout << "Wrote " << bytesWritten << " bytes in " << recWrite << " records using " 
       << passCount << " passes through the input data" <<  endl;
}

void writeFooter( ostream* outRef, struct tm* timeBase ) {
  struct recHeader recHead;
  recHead.type = (unsigned char)REC_FOOTER;
  recHead.length = htons( sizeof(recHeader) + sizeof(GpehFooter));

  struct GpehFooter footer;
  footer.year  = htons(timeBase->tm_year + 1900);
  footer.month = (unsigned char)(timeBase->tm_mon + 1);
  footer.day   = (unsigned char)timeBase->tm_mday;
  footer.hour  = (unsigned char)timeBase->tm_hour;
  footer.min   = (unsigned char)timeBase->tm_min;
  footer.sec   = (unsigned char)timeBase->tm_sec;   

  writeRec( outRef, &recHead, (unsigned char*)&footer );
}


int main( int argc, char* argv[]  )
{
  ios::sync_with_stdio(false);

  char inFile[1024], outFile[1024];
  struct tm timeBase;
  unsigned int fmtVer;
  int step = 1;
  unsigned int targetSize = 0;
  unsigned int randomBytes = 0;
  unsigned int scannerID = 0;
  
  int opt;
  while ( (opt = getopt(argc, argv, "vi:o:t:s:d:f:z:r:c:")) != -1) 
    {
      switch (opt) 
	{
	case 'v':
	  cout << "Version: " << svn_id << endl;
	  return 0;

	case 'i':
	  strcpy(inFile, optarg);
	  break;

	case 'o':
	  strcpy(outFile, optarg);
	  break;

	case 't':
	  strptime(optarg, "%Y%m%d%H%M%S", &timeBase);
	  break;

	case 's':
	  step = atoi(optarg);
	  break;

	case 'd' :
	  debug = atoi(optarg);
	  break;
	case 'f':
          fmtVer = atoi(optarg);
	  break;
	  
	case 'z':
	  targetSize = atoi(optarg);
	  break;
	  
	case 'r':
	  randomBytes = atoi(optarg);
	  break;

	case 'c':
	  scannerID = (unsigned int)strtol(optarg,NULL,0);
	  break;

	default: /* ’?’ */
          fprintf(stderr, "Unknown option \"%c\"\n", opt);
	  fprintf(stderr, "Usage: %s -i inFile -o outFile -t time [-f fmtVer]\n",
		  argv[0]);
	  exit(1);
	}
    }


  ifstream in (inFile, ios::binary);
  if (! in.is_open() )
    {
      cout << "Unable to open file" << inFile << "\n";
      return 1;
    }
  if ( debug > 9 ) cout << "in.tellg=" << in.tellg() << endl;

  ostream* outRef;
  ofstream out;
  if ( strcmp("-", outFile) == 0 )    
    outRef = &cout;
  else
    {
      out.open(outFile, ios::binary);
      if (! out.is_open() )
	{
	  cout << "Unable to open file" << outFile << "\n";
	  return 1;
	}
      outRef = &out;
    }

  if ( debug > 5 ) { 
    cout << "main: sizeof(recHeader)= " << sizeof(recHeader) << endl;
  }
  
  if ( targetSize == 0 ) {
    updateTimeStamps( in, outRef, &timeBase, step, fmtVer );
    writeFooter( outRef, &timeBase );
  } else {
    makeFile( in, outRef, targetSize, fmtVer, randomBytes, scannerID );
  }

  in.close();
  
  outRef->flush();

  if ( out.is_open() )    
    out.close();

  return 0;
}

  
	      

	  
