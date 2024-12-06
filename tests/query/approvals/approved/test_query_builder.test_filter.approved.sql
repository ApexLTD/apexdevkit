
            EXECUTE AS USER = 'John'
            SELECT [item_id] AS [id], [item_name] AS [name], [date] AS [date]
            FROM TABLE

            ORDER BY date DESC
            OFFSET 2400 ROWS FETCH NEXT 100 ROWS ONLY
