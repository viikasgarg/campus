-- A non-updatable view to simplify SQL based reports
create view sword.work_study_student as
select *, firstname as fname, lastname as lname from work_study_studentworker
left join profiles_student on profiles_student.mdluser_ptr_id = work_study_studentworker.student_ptr_id
left join mdl_user on mdl_user.id = profiles_student.mdluser_ptr_id
where mdl_user.inactive=0;
