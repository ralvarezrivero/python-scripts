$A = 22,5,'whatever',8,12,9.1,'last'
Write-Host($A[-1])

function combine{
    Param(
        $a,
        $b,
        $c
    )

    Write-Host "Parameter 1 = $a, Parameter 2 = $b, Parameter 3 = $c"
}

combine one two three