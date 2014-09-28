SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';


-- -----------------------------------------------------
-- Table `usr`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `usr` ;

CREATE  TABLE IF NOT EXISTS `usr` (
  `USR_ID` INT(19) NOT NULL AUTO_INCREMENT ,
  `USERNAME` VARCHAR(150) NOT NULL ,
  `PWD_HASH` VARCHAR(100) NOT NULL ,
  `FAILED_LOGINS` INT(10) NOT NULL ,
  `FNAME` VARCHAR(100) NOT NULL ,
  `LNAME` VARCHAR(100) NOT NULL ,
  `EMAIL` VARCHAR(100) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `CREATED_BY` VARCHAR(160) NULL DEFAULT NULL ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `LAST_UPD_BY` VARCHAR(160) NULL DEFAULT NULL ,
  PRIMARY KEY (`USR_ID`) ,
  UNIQUE INDEX `USERNAME` (`USERNAME` ASC) ,
  UNIQUE INDEX `EMAIL` (`EMAIL` ASC) )
ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `personal_details`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `personal_details` ;

CREATE  TABLE IF NOT EXISTS `personal_details` (
  `USR_ID` INT(19) NOT NULL ,
  `FNAME` VARCHAR(400) NOT NULL ,
  `MNAME` VARCHAR(400) NULL DEFAULT NULL ,
  `LNAME` VARCHAR(400) NULL DEFAULT NULL ,
  `EMAIL` VARCHAR(1000) NOT NULL ,
  `SEX` VARCHAR(50) NOT NULL ,
  `Birth_Date` DATE NOT NULL ,
  `HOME_PHONE` VARCHAR(50) NOT NULL ,
  `MOBILE_PHONE` VARCHAR(50) NOT NULL ,
  `FAX` VARCHAR(50) NOT NULL ,
  `ADDR_ID` INT(19) NOT NULL AUTO_INCREMENT ,
  `PROFILE_IMAGE` LONGBLOB NULL DEFAULT NULL ,
  UNIQUE INDEX `USR_ID` (`USR_ID` ASC) ,
  UNIQUE INDEX `ADDR_ID` (`ADDR_ID` ASC) ,
  CONSTRAINT `FK_usrid_personal`
    FOREIGN KEY (`USR_ID` )
    REFERENCES `usr` (`USR_ID` ))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `addr`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `addr` ;

CREATE  TABLE IF NOT EXISTS `addr` (
  `ADDR_ID` INT(19) NOT NULL ,
  `ADDR1` VARCHAR(1000) NOT NULL ,
  `ADDR2` VARCHAR(1000) NULL DEFAULT NULL ,
  `ADDR3` VARCHAR(1000) NULL DEFAULT NULL ,
  `CITY` VARCHAR(400) NOT NULL ,
  `STATE` VARCHAR(400) NOT NULL ,
  `COUNTRY` VARCHAR(400) NOT NULL ,
  `ZIPCODE` VARCHAR(50) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `CREATED_BY` VARCHAR(160) NULL DEFAULT NULL ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `LAST_UPD_BY` VARCHAR(160) NULL DEFAULT NULL ,
  PRIMARY KEY (`ADDR_ID`) ,
  CONSTRAINT `FK_addr_id`
    FOREIGN KEY (`ADDR_ID` )
    REFERENCES `personal_details` (`ADDR_ID` ))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `class_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `class_mst` ;

CREATE  TABLE IF NOT EXISTS `class_mst` (
  `class_id` INT(19) NOT NULL AUTO_INCREMENT ,
  `class_name` VARCHAR(150) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `CREATED_BY` VARCHAR(160) NULL DEFAULT NULL ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `LAST_UPD_BY` VARCHAR(160) NULL DEFAULT NULL ,
  PRIMARY KEY (`class_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `course_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `course_mst` ;

CREATE  TABLE IF NOT EXISTS `course_mst` (
  `course_id` INT(11) NOT NULL AUTO_INCREMENT ,
  `course_name` VARCHAR(45) NULL DEFAULT NULL ,
  `course_teacher_id` INT(11) NULL DEFAULT NULL ,
  `course_credit` VARCHAR(5) NULL DEFAULT NULL ,
  `course_class` VARCHAR(45) NULL DEFAULT NULL ,
  `course_term` VARCHAR(5) NULL DEFAULT NULL ,
  PRIMARY KEY (`course_id`) )
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `edu`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `edu` ;

CREATE  TABLE IF NOT EXISTS `edu` (
  `edu_id` INT(19) NOT NULL AUTO_INCREMENT ,
  `edu_course` VARCHAR(200) NOT NULL ,
  `specialization` VARCHAR(100) NOT NULL ,
  `certi_path` VARCHAR(100) NULL DEFAULT NULL ,
  `institute` VARCHAR(500) NOT NULL ,
  `passing_year` DATE NOT NULL ,
  PRIMARY KEY (`edu_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `location_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `location_mst` ;

CREATE  TABLE IF NOT EXISTS `location_mst` (
  `location_id` INT(11) NOT NULL ,
  `location_desc` VARCHAR(45) NULL DEFAULT NULL ,
  PRIMARY KEY (`location_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `stdnt_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stdnt_mst` ;

CREATE  TABLE IF NOT EXISTS `stdnt_mst` (
  `stdnt_id` INT(11) NOT NULL ,
  `stdnt_name` VARCHAR(45) NULL DEFAULT NULL ,
  `stdnt_course_id` INT(11) NULL DEFAULT NULL ,
  `stdnt_mob_no` VARCHAR(45) NULL DEFAULT NULL ,
  `stdnt_mail_id` VARCHAR(45) NULL DEFAULT NULL ,
  `stdnt_term` VARCHAR(5) NULL DEFAULT NULL ,
  PRIMARY KEY (`stdnt_id`) ,
  INDEX `stdnt_course_frgn_key0` (`stdnt_course_id` ASC) ,
  CONSTRAINT `stdnt_course_frgn_key0`
    FOREIGN KEY (`stdnt_course_id` )
    REFERENCES `course_mst` (`course_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `teacher_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `teacher_mst` ;

CREATE  TABLE IF NOT EXISTS `teacher_mst` (
  `teacher_id` INT(19) NOT NULL AUTO_INCREMENT ,
  `teacher_name` VARCHAR(150) NOT NULL ,
  `teacher_course_id` INT(11) NULL DEFAULT NULL ,
  `teacher_emailId` VARCHAR(45) NULL DEFAULT NULL ,
  `teacher_mob_no` INT(11) NULL DEFAULT NULL ,
  PRIMARY KEY (`teacher_id`) )
ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `matrix_mapping_data`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `matrix_mapping_data` ;

CREATE  TABLE IF NOT EXISTS `matrix_mapping_data` (
  `mapping_cell_id` INT(11) NOT NULL ,
  `student_id` INT(11) NULL DEFAULT NULL ,
  `course_id` INT(11) NULL DEFAULT NULL ,
  `teacher_id` INT(11) NULL DEFAULT NULL ,
  `location_id` INT(11) NULL DEFAULT NULL ,
  PRIMARY KEY (`mapping_cell_id`) ,
  INDEX `fk_matrix_stdnt_id` (`student_id` ASC) ,
  INDEX `fk_matrix_course_id` (`course_id` ASC) ,
  INDEX `fk_matrix_teacher_id` (`teacher_id` ASC) ,
  INDEX `fk_matrix_location_id` (`location_id` ASC) ,
  CONSTRAINT `fk_matrix_course_id`
    FOREIGN KEY (`course_id` )
    REFERENCES `course_mst` (`course_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_matrix_location_id`
    FOREIGN KEY (`location_id` )
    REFERENCES `location_mst` (`location_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_matrix_stdnt_id`
    FOREIGN KEY (`student_id` )
    REFERENCES `stdnt_mst` (`stdnt_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_matrix_teacher_id`
    FOREIGN KEY (`teacher_id` )
    REFERENCES `teacher_mst` (`teacher_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `notfication_dtl`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `notfication_dtl` ;

CREATE  TABLE IF NOT EXISTS `notfication_dtl` (
  `notify_id` INT(11) NOT NULL AUTO_INCREMENT ,
  `notification_msg` VARCHAR(250) NULL DEFAULT NULL ,
  `to_id` INT(4) NULL DEFAULT NULL ,
  `flag` VARCHAR(2) NULL DEFAULT NULL ,
  `process_flag` VARCHAR(2) NULL DEFAULT NULL ,
  PRIMARY KEY (`notify_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `session_code_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `session_code_mst` ;

CREATE  TABLE IF NOT EXISTS `session_code_mst` (
  `session_code` VARCHAR(45) NOT NULL ,
  `course` VARCHAR(45) NULL DEFAULT NULL ,
  `credit` INT(11) NULL DEFAULT NULL ,
  `venue` INT(11) NULL DEFAULT NULL ,
  `instructor` VARCHAR(45) NULL DEFAULT NULL ,
  PRIMARY KEY (`session_code`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `session_hdr_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `session_hdr_mst` ;

CREATE  TABLE IF NOT EXISTS `session_hdr_mst` (
  `session_hdr_id` INT(11) NOT NULL ,
  `session_col` VARCHAR(45) NULL DEFAULT NULL ,
  `session_time` VARCHAR(45) NULL DEFAULT NULL ,
  PRIMARY KEY (`session_hdr_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `sub_class_teacher_mapping`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `sub_class_teacher_mapping` ;

CREATE  TABLE IF NOT EXISTS `sub_class_teacher_mapping` (
  `sub_id` INT(19) NOT NULL ,
  `teacher_id` INT(19) NOT NULL ,
  `class_id` INT(19) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `CREATED_BY` VARCHAR(160) NULL DEFAULT NULL ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `LAST_UPD_BY` VARCHAR(160) NULL DEFAULT NULL ,
  UNIQUE INDEX `sub_class_teacher_id` (`sub_id` ASC, `teacher_id` ASC, `class_id` ASC) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `sub_mst`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `sub_mst` ;

CREATE  TABLE IF NOT EXISTS `sub_mst` (
  `sub_id` INT(19) NOT NULL AUTO_INCREMENT ,
  `sub_name` VARCHAR(150) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `CREATED_BY` VARCHAR(160) NULL DEFAULT NULL ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `LAST_UPD_BY` VARCHAR(160) NULL DEFAULT NULL ,
  PRIMARY KEY (`sub_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `timetable`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `timetable` ;

CREATE  TABLE IF NOT EXISTS `timetable` (
  `idTimeTable` INT(11) NOT NULL ,
  `month` VARCHAR(15) NULL DEFAULT NULL ,
  `day` INT(11) NULL DEFAULT NULL ,
  `date` VARCHAR(45) NULL DEFAULT NULL ,
  `year` INT(11) NULL DEFAULT NULL ,
  `session1` VARCHAR(45) NULL DEFAULT NULL ,
  `session2` VARCHAR(45) NULL DEFAULT NULL ,
  `session3` VARCHAR(45) NULL DEFAULT NULL ,
  `session4` VARCHAR(45) NULL DEFAULT NULL ,
  `session5` VARCHAR(45) NULL DEFAULT NULL ,
  `session6` VARCHAR(45) NULL DEFAULT NULL ,
  `session7` VARCHAR(45) NULL DEFAULT NULL ,
  `session8` VARCHAR(45) NULL DEFAULT NULL ,
  PRIMARY KEY (`idTimeTable`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `usr_edu`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `usr_edu` ;

CREATE  TABLE IF NOT EXISTS `usr_edu` (
  `USR_ID` INT(19) NOT NULL ,
  `Edu_id` INT(19) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  UNIQUE INDEX `uq_usr_edu` (`USR_ID` ASC, `Edu_id` ASC) ,
  INDEX `FK_edu_id` (`Edu_id` ASC) ,
  CONSTRAINT `FK_edu_id`
    FOREIGN KEY (`Edu_id` )
    REFERENCES `edu` (`edu_id` ),
  CONSTRAINT `FK_usr_id`
    FOREIGN KEY (`USR_ID` )
    REFERENCES `usr` (`USR_ID` ))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `usr_pwd_hsty`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `usr_pwd_hsty` ;

CREATE  TABLE IF NOT EXISTS `usr_pwd_hsty` (
  `USR_PWD_HSTY_ID` INT(19) NOT NULL AUTO_INCREMENT ,
  `USR_ID` INT(19) NULL DEFAULT NULL ,
  `OLD_PWD` VARCHAR(255) NOT NULL ,
  `CLIENT_IP_ADDR` VARCHAR(40) NOT NULL ,
  `SERVER_IP_ADDR` VARCHAR(40) NOT NULL ,
  `ENTRYPOINT_URL` VARCHAR(1000) NOT NULL ,
  `ENTRY_TIME` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  PRIMARY KEY (`USR_PWD_HSTY_ID`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `work`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `work` ;

CREATE  TABLE IF NOT EXISTS `work` (
  `work_id` INT(19) NOT NULL AUTO_INCREMENT ,
  `company_name` VARCHAR(200) NOT NULL ,
  `designation` VARCHAR(200) NOT NULL ,
  `job_profile` VARCHAR(1000) NOT NULL ,
  `joining_date` DATE NOT NULL ,
  `leaving_date` DATE NOT NULL ,
  PRIMARY KEY (`work_id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `usr_work`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `usr_work` ;

CREATE  TABLE IF NOT EXISTS `usr_work` (
  `USR_ID` INT(19) NOT NULL ,
  `work_id` INT(19) NOT NULL ,
  `EXPERIENCE_YEARS` INT(5) NOT NULL ,
  `CR_DATE` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `LAST_UPD` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  UNIQUE INDEX `uq_usr_work1` (`USR_ID` ASC, `work_id` ASC) ,
  INDEX `FK_work_id1` (`work_id` ASC) ,
  CONSTRAINT `FK_usr_id1`
    FOREIGN KEY (`USR_ID` )
    REFERENCES `usr` (`USR_ID` ),
  CONSTRAINT `FK_work_id1`
    FOREIGN KEY (`work_id` )
    REFERENCES `work` (`work_id` ))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
