import numpy as np

import Util as Ut

class BlockTTtensor:
    def __init__(self,U,basis,tensordir="./"):
        ''' This class serves for the representation of several high-dimensional functions
        in the block-TT-format.
        
        Parameters:
        ------------
        U: List of component tensors, LENGTH d, where d is the dimension of the tensor. The first element
            should be a fourth order tensor. Its last index yields the number of functions represented by
            the block-TT-tensor. All others are third order tensors.
        basis: A list of pyemma-reader objects. Each reader contains the evaluation of the one-coordinate basis
            for one specific coordinate.
        tensordir: String, directory where intermediate evaluations are stored. Defaults to the current directory.
        '''
        # Make the inputs generally known:
        self.U = U
        self.basis = basis
        self.tensordir = tensordir
        # Get the dimensions of the tensor:
        self.d = len(self.U)
        # Define the root:
        self.root = 0
        # Define the number of eigenfunctions:
        self.M = np.shape(self.U[0])[3]
        # Extract the ranks:
        self.R = np.zeros(self.d-1)
        for k in range(self.d-1):
            self.R[k] = self.U[k].shape[2]
        # Compute the initial interfaces:
        self.interfaces = self.ComputeInterfaces()
    def GetRanks(self,k=-1):
        ''' Return k-th TT-rank or a vector of all TT-ranks, if k is not given.
        
        Parameters:
        ------------
        k: int, the index of the rank which is required. If k is not given, a
            vector of all ranks is returned.
        
        Returns
        ----------
        R: int or nd-array(self.d-1,).
        '''
        if k>=0 or k<=(self.d-2):
            return self.R[k]
        else:
            return self.R
    def GetRankTriple(self,k):
        ''' Return the triple of basis set sizes for component k, i.e the triple
        (r_k-1,n,r_k).
        '''
        if k == self.root:
            return self.U[k].shape[:3]
        else:
            return self.U[k].shape
    def ComponentBasis(self,k):
        ''' Return the component time series for component k
        
        Parameters:
        -------------
        k, integer, the component for which the time series is required.
        
        Returns:
        -------------
        pyemma-reader, the time series for this component. 
        '''
        return self.basis[k]
    def ComponentTensor(self,k,order=0):
        ''' Return the component tensor for component k
        
        Parameters:
        -------------
        k, integer, the component whose component tensor is required.
        order: Can be 0,1,2. order=0 means that the component is returned as a
            third order tensor, while order=1 returns the left unfolding ans
            order=2 returns the right unfolding. However, this will be ignored
            if k is the root.
        
        Returns:
        -------------
        U: ndarray, SHAPE (r_{p-1},n_p,r_p), the component tensor for
            component k.
        '''
        if order == 1 and not k == self.root:
            dims = self.GetRankTriple(k)
            return np.reshape(self.U[k],(dims[0]*dims[1],dims[2]))
        elif order == 2 and not k == self.root:
            dims = self.GetRankTriple(k)
            return np.reshape(self.U[k],(dims[0],dims[1]*dims[2]))
        else:
            return self.U[k]
    def SetComponentTensor(self,k,U):
        ''' Set the component tensor for component k
        
        Parameters:
        -------------
        k, integer, the component whose component tensor is required.
        U: ndarray, SHAPE (r_{p-1},n,r_p), the new component tensor for
            component k.
        '''
        self.U[k] = U
    def GetInterface(self,k):
        ''' Get the interface for component k.
        
        Parameters;
        ------------
        k, integer, the component whose interface is required.
        
        Returns:
        ------------
        pyemma-reader, the interface at component k.
        '''
        return self.interfaces[k]
    def SetInterface(self,k,intf):
        ''' Set the interface for component k.
        
        Parameters;
        ------------
        k, integer, the component whose interface is to be renewed.
        intf: pyemma-reader, the new interface at component k.
        '''
        self.interfaces[k] = intf    
    def ComputeInterfaces(self):
        ''' Evaluate interfaces of the tensor and return them. This function
        first computes all the left interfaces from position zero to the root,
        then it computes all right interfaces from position d-1 down to the root. 
             
        Returns:
        ------------
        List of pyemma-readers, containing the interfaces:
        '''
        interface_list = []
        # Loop from position zero up to the root:
        for k in range(self.root):
            # Get the componnet tensor for this coordinate:
            Uk = self.ComponentTensor(k,order=1)
            # Get the component basis for this coordinate:
            Fk = self.ComponentBasis(k)
            # Compute all products between this basis and the last interface:
            if k == 0:
                Yk = Ut.ApplyLinearTransform(Fk,Uk,self.tensordir+"Interface%d"%k)
            else:
                Yk = Ut.DoubleProducts(Yk,Fk,self.tensordir+"Interface%d"%k,Uk)
            interface_list.append(Yk)
        # Loop from final position down to the loop. We collect all the readers
        # for the right part separately.
        backward_list = []
        for k in range(self.d-2,self.root-1,-1):
            # Get the componnet tensor for this coordinate:
            Uk = self.ComponentTensor(k+1,order=2)
            # Get the component basis for this coordinate:
            Fk = self.ComponentBasis(k+1)
            # Compute all products between this basis and the last interface:
            if k == (self.d-2):
                Yk = Ut.ApplyLinearTransform(Fk,Uk.transpose(),self.tensordir+"Interface%d"%k)
            else:
                Yk = Ut.DoubleProducts(Fk,Yk,self.tensordir+"Interface%d"%k,Uk.transpose())
            backward_list.insert(0,Yk)
        # Glue the two lists together:
        interface_list = interface_list + backward_list
        return interface_list