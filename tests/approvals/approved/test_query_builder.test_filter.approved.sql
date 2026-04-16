
            EXECUTE AS USER = 'John'
            SELECT [item_id] AS [id], [item_name] AS [name], [date]
            FROM TABLE
            WHERE (([item_id] LIKE N'begin%') OR ([item_name] LIKE N'%end'))
            ORDER BY date DESC
            OFFSET 2400 ROWS FETCH NEXT 100 ROWS ONLY
