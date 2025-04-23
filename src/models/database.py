import os

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config.logging_config import setup_logging

# 로깅 설정
logger = setup_logging(__name__)

# Load environment variables
load_dotenv()

# Database connection URL
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class BizSupport(Base):
    __tablename__ = "tb_bizup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sme_subvention_id = Column(String(50))
    title_name = Column(String(300))
    reception_institution_name = Column(String(300))
    reception_start_date = Column(String(50))
    reception_end_date = Column(String(50))
    support_amount = Column(String(100))
    registered_at = Column(String(50))
    modified_at = Column(String(50))
    notice_date = Column(String(50))
    area_name = Column(String(300))
    url_address = Column(String(2048))
    business_overview_content = Column(Text)
    support_qualification_content = Column(Text)
    support_content = Column(Text)
    application_way_content = Column(String(4000))
    responsible_division_name = Column(String(300))
    responsible_person_name = Column(String(100))
    responsible_person_email = Column(String(100))
    tel_number = Column(String(100))
    original_file_name = Column(String(300))
    file_path = Column(String(2048))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Create all tables
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블이 생성되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 테이블 생성 중 오류 발생: {str(e)}")
        raise


# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {str(e)}")
        raise
    finally:
        db.close()
        logger.debug("데이터베이스 세션이 종료되었습니다.")
