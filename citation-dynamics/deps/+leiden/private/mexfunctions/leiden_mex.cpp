#include "leiden.hpp"

#include "mex.h"

#define ERROR(message)                              \
{                                                   \
    mexErrMsgIdAndTxt ("Leiden:error", message) ;   \
}


#define USAGE "usage: [...] = leiden(...) ; signature: 18 inputs & 1 or 2 outputs"

void usage_info       // check usage
(
    bool ok,                // if false, then usage is not correct
    const char *message     // error message if usage is not correct
)
{

  if (!ok) {
    ERROR (message) ;
  }

}

void parseInputs
(
 mwIndex **ij,
 double  **v,
 mwSize *n,
 mwSize *m,
 char **func,
 double *gamma,
 int *isdirected,
 mwIndex **cid_init,
 double *ha_shift,
 double *ha_scale,
 double *hr_shift,
 double *hr_scale,
 mwSize *n_iter,
 int *psik,
 double *psic,
 double *ka,
 int *seed,
 mwSize *n_piter,
 mwSize *n_oiter,
 const mxArray *pargin [ ],
 const int nargin
){

  *ij = ( (mwIndex*) mxGetPr( pargin[0] ) );

  // starting index of each column
  *v  = mxGetPr( pargin[1] );

  // number of columns in the matrix
  *n  = mwSize( mxGetScalar( pargin[2] ) );

  // number of edges
  *m  = mwSize( mxGetScalar( pargin[3] ) );

  *func  = mxArrayToString( pargin[4] );

  *gamma  = double( mxGetScalar( pargin[5] ) );

  *isdirected = int( mxGetScalar( pargin[6] ) );

  if ( mxGetNumberOfElements( pargin[7] ) > 0 )
    *cid_init = ( (mwIndex*) mxGetPr( pargin[7] ) );
  else
    *cid_init = NULL;

  *ha_shift = double( mxGetScalar( pargin[8] ) );

  *ha_scale = double( mxGetScalar( pargin[9] ) );

  *hr_shift = double( mxGetScalar( pargin[10] ) );

  *hr_scale = double( mxGetScalar( pargin[11] ) );

  *n_iter = mwSize( mxGetScalar( pargin[12] ) );

  *psik = int( mxGetScalar( pargin[13] ) );

  *psic = double( mxGetScalar( pargin[14] ) );

  *ka = double( mxGetScalar( pargin[15] ) );

  *seed = int( mxGetScalar( pargin[16] ) );

  *n_piter = mwSize( mxGetScalar( pargin[17] ) );

  *n_oiter = mwSize( mxGetScalar( pargin[18] ) );
}

void mexFunction
(
 int nargout,
 mxArray *pargout [ ],
 int nargin,
 const mxArray *pargin [ ]
 )
{

  mwSize n, m, n_iter, n_piter, n_oiter;
  double gamma, quality = 0.0;
  mwIndex *ij;
  double *v;
  mwIndex *cid;
  mwIndex *cid_init;
  char *func;
  int isdirected;
  int psik;
  int seed;
  double psic, ka;
  double ha_shift, ha_scale, hr_shift, hr_scale;

  usage_info (nargin == 19 && nargout >= 1 && nargout <= 2, USAGE) ;

  parseInputs( &ij, &v, &n, &m, &func, &gamma, &isdirected, &cid_init,
               &ha_shift, &ha_scale, &hr_shift, &hr_scale, &n_iter,
               &psik, &psic, &ka, &seed, &n_piter, &n_oiter,
               pargin, nargin );

  pargout[0] = mxCreateNumericMatrix(n, 1, mxINT64_CLASS, mxREAL);
  cid = (mwIndex *) mxGetPr(pargout[0]);

  // mexPrintf( "Called MEX (%g, %d, %d, %s, %g, %g, %d)\n", quality, n, m, func, gamma, double( mxGetInf() ), isdirected );

  const mwSize * cid_out = do_leiden( &quality,
                                      ij,
                                      v,
                                      cid_init,
                                      n,
                                      m,
                                      func, gamma,
                                      seed,
                                      isdirected,     // 0:undirected  1:directed
                                      double( mxGetInf() ),
                                      psik, psic, ka,
                                      ha_shift, ha_scale,
                                      hr_shift, hr_scale,
                                      n_iter, n_piter, n_oiter );

  if (cid_out != NULL){
    for (int i = 0; i < n; i++){
      cid[i] = cid_out[i] + 1;
    }
    free( (mwSize *)cid_out );
  }

  if (nargout == 2)
    pargout[1] = mxCreateDoubleScalar(quality);

  return;

}
