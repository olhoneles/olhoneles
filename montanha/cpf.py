# Downloaded from http://wiki.python.org.br/Cpf
# License: CC-BY http://creativecommons.org/licenses/by/2.5/br/


class Cpf:
    def __init__( self ):
        """
        Class to interact with CPF numbers
        """
        pass

    def format( self, cpf ):
        """
        Method that formats a brazilian CPF

        Tests:
        >>> print Cpf().format('91289037736')
        912.890.377-36
        """
        return "%s.%s.%s-%s" % ( cpf[0:3], cpf[3:6], cpf[6:9], cpf[9:11] )

    def validate( self, cpf ):
        """
        Method to validate a brazilian CPF number
        Based on Pedro Werneck source avaiable at
        www.PythonBrasil.com.br

        Tests:
        >>> print Cpf().validate('91289037736')
        True
        >>> print Cpf().validate('91289037731')
        False
        """
        cpf_invalidos = [11*str(i) for i in range(10)]
        if cpf in cpf_invalidos:
            return False

        if not cpf.isdigit():
            """ Verifica se o CPF contem pontos e hifens """
            cpf = cpf.replace( ".", "" )
            cpf = cpf.replace( "-", "" )

        if len( cpf ) < 11:
            """ Verifica se o CPF tem 11 digitos """
            return False

        if len( cpf ) > 11:
            """ CPF tem que ter 11 digitos """
            return False

        selfcpf = [int( x ) for x in cpf]

        cpf = selfcpf[:9]

        while len( cpf ) < 11:

            r =  sum( [( len( cpf )+1-i )*v for i, v in [( x, cpf[x] ) for x in range( len( cpf ) )]] ) % 11

            if r > 1:
                f = 11 - r
            else:
                f = 0
            cpf.append( f )


        return bool( cpf == selfcpf )

