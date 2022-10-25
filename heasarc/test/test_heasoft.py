
import os
import sys
import glob
from astropy.io import fits as pyfits


class HeasoftError(Exception):
    pass



class TestHeasoft:
    
    def __init__(cls):
        """setting up"""
        
        cls.rxte_basedir = ('/home/idies/workspace/headata/'
                            'FTP/rxte/data/archive')
        cls.rxte_obsid   = '80001-01-01-10'
        cls.rxte_outdir  = f'tmp.{cls.rxte_obsid}'
        
        os.system(f'mkdir -p {cls.rxte_outdir}')
        
    def _cleanup(cls):
        os.system(f'rm -rf {cls.rxte_outdir}')
    
    def test_conda_env(self):
        """Test we are in heasoft conda env"""
        
        if not 'CONDA_PREFIX' in os.environ:
            raise HeasoftError('CONDA_PREFIX is not defined. conda is not setup correctly')
        
        env = os.environ['CONDA_PREFIX'].split('/')[-1]
        if not env == 'heasoft':
            raise HeasoftError('It does not look like this is the (heaosft) conda environment.')
    
    def test_env(self):
        """Test envirenment vairables are set"""

        if not 'HEADAS' in os.environ:
            raise HeasoftError('The environmental vairable HEADAS is not defined')

        if not 'CALDB' in os.environ:
            raise HeasoftError('The environmental vairable CALDB is not defined')
        
        
    def test_pyxspec(self):
        """Test pyxspec can be imported"""
        try:
            import xspec
        except:
            raise HeasoftError('pyxspec cannot be imported')
        
    def test_heasoftpy(self):
        """Test heasofpy can be imported"""
        try:
            import heasoftpy  
        except:
            raise HeasoftError('heasoftpy cannot be imported')
    
    def test_caldbinfo(self):
        """Test a call to caldb works"""
        if os.system('caldbinfo BASIC'):
            raise HeasoftError('caldbinfo failed!')


    def test_fhelp_call(self):
        """Test a call to fhelp works"""
        if os.system('fhelp fdump pager=cat'):
            raise HeasoftError('fhelp failed!')
        
        
    def test_rxte_pipeline(self):
        """test a call to rxte data reduction"""
        
        import heasoftpy as hsp
        
        basedir = self.rxte_basedir 
        obsid   = self.rxte_obsid
        outdir  = self.rxte_outdir
        obsdir  = f'{basedir}/AO{obsid[0]}/P{obsid[0:5]}/{obsid}'
                
        result = hsp.pcaprepobsid(indir=obsdir, outdir=outdir, 
                                  modelfile='CALDB', datamodes='Standard2')
        if result.returncode != 0 or 'error' in '\n'.join(result.output).lower():
            # note that pcaprepobsid doesn't return correctly
            raise HeasoftError('pcaprepobsid failed!\n' + 
                               '\n'.join(result.output))

        
        filt_expr = ('(ELV > 4) && (OFFSET < 0.1) && (NUM_PCU_ON > 0) '
                     '&& .NOT. ISNULL(ELV) && (NUM_PCU_ON < 6)')
        filt_file = glob.glob(outdir+"/FP_*.xfl")[0]
 

        result = hsp.maketime(infile = filt_file, 
                              outfile = f'{outdir}/example.gti',
                              expr = filt_expr, name='NAME', 
                              value='VALUE', time='TIME', compact='NO', clobber='yes')
        if result.returncode != 0:
            raise HeasoftError('maketime in test_rxte_pipeline failed!\n' + 
                               '\n'.join(result.output))

        
        # extract light curve #
        result = hsp.pcaextlc2(src_infile=f'@{outdir}/FP_dtstd2.lis',
                               bkg_infile=f'@{outdir}/FP_dtbkg2.lis',
                               outfile=f'{outdir}/example.lc', 
                               gtiandfile=f'{outdir}/example.gti',
                               pculist='ALL', layerlist='ALL', binsz=16)
        if result.returncode != 0:
            raise HeasoftError('pcaextlc2 in test_rxte_pipeline failed!\n' + 
                               '\n'.join(result.output))
    
        with pyfits.open(os.path.join(outdir,'example.lc'), memmap=False) as hdul:
            lc=hdul[1].data
    


if __name__ == '__main__':
    
    tester = TestHeasoft()
    
    tester.test_conda_env()
    tester.test_env()
    tester.test_pyxspec()
    tester.test_heasoftpy()
    tester.test_caldbinfo()
    tester.test_fhelp_call()
    tester.test_rxte_pipeline()
    
    tester._cleanup()