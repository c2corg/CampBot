Select * from (

select count(1) as contribs, user_id, substr(written_at,0,5) as year
from contribution
where type!='i'
group by user_id, year
order by contribs DESC)

where contribs > 12