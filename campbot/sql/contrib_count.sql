SELECT * FROM (
	SELECT user_id, count(1) AS contribs FROM (
		SELECT * FROM contribution
		WHERE type!="i" AND written_at < "2018-06-01"
		GROUP BY document_id, user_id
	)
	GROUP BY user_id
	ORDER BY contribs DESC
)
WHERE contribs >= 1