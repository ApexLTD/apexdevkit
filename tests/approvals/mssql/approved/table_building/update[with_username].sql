EXECUTE AS USER = 'test'
UPDATE [test].[apples]
SET
    clr = red
WHERE [apid] = 1
REVERT
