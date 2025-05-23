USE [master]
GO
/****** Object:  Database [TextileShopDB]    Script Date: 4/27/2025 5:54:51 PM ******/
CREATE DATABASE [TextileShopDB]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'TextileShopDB', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\TextileShopDB.mdf' , SIZE = 8192KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'TextileShopDB_log', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\TextileShopDB_log.ldf' , SIZE = 8192KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT
GO
ALTER DATABASE [TextileShopDB] SET COMPATIBILITY_LEVEL = 150
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [TextileShopDB].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [TextileShopDB] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [TextileShopDB] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [TextileShopDB] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [TextileShopDB] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [TextileShopDB] SET ARITHABORT OFF 
GO
ALTER DATABASE [TextileShopDB] SET AUTO_CLOSE ON 
GO
ALTER DATABASE [TextileShopDB] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [TextileShopDB] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [TextileShopDB] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [TextileShopDB] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [TextileShopDB] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [TextileShopDB] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [TextileShopDB] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [TextileShopDB] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [TextileShopDB] SET  ENABLE_BROKER 
GO
ALTER DATABASE [TextileShopDB] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [TextileShopDB] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [TextileShopDB] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [TextileShopDB] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [TextileShopDB] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [TextileShopDB] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [TextileShopDB] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [TextileShopDB] SET RECOVERY SIMPLE 
GO
ALTER DATABASE [TextileShopDB] SET  MULTI_USER 
GO
ALTER DATABASE [TextileShopDB] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [TextileShopDB] SET DB_CHAINING OFF 
GO
ALTER DATABASE [TextileShopDB] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [TextileShopDB] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [TextileShopDB] SET DELAYED_DURABILITY = DISABLED 
GO
ALTER DATABASE [TextileShopDB] SET ACCELERATED_DATABASE_RECOVERY = OFF  
GO
ALTER DATABASE [TextileShopDB] SET QUERY_STORE = OFF
GO
USE [TextileShopDB]
GO
/****** Object:  Table [dbo].[accounts]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[accounts](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[customer_id] [int] NOT NULL,
	[order_id] [int] NOT NULL,
	[name] [varchar](100) NOT NULL,
	[account_no] [varchar](30) NOT NULL,
	[ifsc_no] [varchar](20) NOT NULL,
	[payment_status] [varchar](20) NOT NULL,
	[bank_name] [varchar](100) NULL,
	[transaction_id] [varchar](255) NULL,
	[cvv] [varchar](4) NULL,
	[expiry_month] [int] NULL,
	[expiry_year] [int] NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[card_transactions]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[card_transactions](
	[transaction_id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NOT NULL,
	[card_number] [varchar](20) NOT NULL,
	[card_holder_name] [varchar](100) NULL,
	[expiry_month] [int] NULL,
	[expiry_year] [int] NULL,
	[cvv] [varchar](4) NULL,
	[transaction_amount] [decimal](10, 2) NOT NULL,
	[transaction_date] [datetime] NULL,
	[merchant_name] [varchar](100) NULL,
	[transaction_type] [varchar](20) NULL,
	[status] [varchar](20) NULL,
	[remarks] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[transaction_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[customers]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[customers](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](100) NULL,
	[phone] [nvarchar](20) NULL,
	[email] [nvarchar](100) NULL,
	[password] [nvarchar](255) NULL,
	[address] [varchar](100) NULL,
	[role] [varchar](555) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[employee_salary]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[employee_salary](
	[salary_id] [int] IDENTITY(1,1) NOT NULL,
	[emp_number] [varchar](50) NOT NULL,
	[basic_salary] [decimal](10, 2) NOT NULL,
	[bonus] [decimal](10, 2) NULL,
	[deductions] [decimal](10, 2) NULL,
	[net_salary]  AS (([basic_salary]+[bonus])-[deductions]),
	[salary_month] [int] NOT NULL,
	[salary_year] [int] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[salary_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[employees]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[employees](
	[emp_id] [int] IDENTITY(1,1) NOT NULL,
	[emp_number] [varchar](50) NOT NULL,
	[name] [varchar](100) NOT NULL,
	[age] [int] NOT NULL,
	[contact_number] [varchar](20) NOT NULL,
	[salary] [decimal](10, 2) NOT NULL,
	[image_url] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[emp_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_emp_number] UNIQUE NONCLUSTERED 
(
	[emp_number] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[offline_orders]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[offline_orders](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[product_id] [int] NOT NULL,
	[quantity] [int] NOT NULL,
	[total_price] [decimal](10, 2) NOT NULL,
	[order_date] [datetime] NULL,
	[created_at] [datetime] NULL,
	[order_group_id] [varchar](100) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[order_items]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[order_items](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NULL,
	[product_id] [int] NULL,
	[quantity] [int] NULL,
	[price] [decimal](10, 2) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[orders]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[orders](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[customer_id] [int] NULL,
	[order_date] [datetime] NULL,
	[total_price] [decimal](10, 2) NULL,
	[status] [nvarchar](50) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[products]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[products](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](100) NULL,
	[category] [varchar](150) NULL,
	[price] [decimal](10, 2) NULL,
	[stock] [nvarchar](150) NULL,
	[image_url] [nvarchar](255) NULL,
	[description] [nvarchar](255) NULL,
	[Pieces] [int] NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[shipments]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[shipments](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NOT NULL,
	[tracking_number] [varchar](50) NULL,
	[carrier] [varchar](50) NULL,
	[shipped_date] [datetime] NULL,
	[estimated_delivery] [datetime] NULL,
	[status] [varchar](50) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[tracking_number] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[SupplierGoods]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[SupplierGoods](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[supplier_number] [varchar](50) NOT NULL,
	[item_name] [varchar](100) NOT NULL,
	[item_value] [decimal](10, 2) NOT NULL,
	[photo_url] [varchar](255) NULL,
	[video_url] [varchar](255) NULL,
	[shop_name] [varchar](100) NULL,
	[shop_address] [varchar](255) NULL,
	[contact] [varchar](100) NULL,
	[item_quantity] [varchar](100) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Suppliers]    Script Date: 4/27/2025 5:54:51 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Suppliers](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[supplier_number] [varchar](50) NOT NULL,
	[name] [varchar](255) NOT NULL,
	[contact] [varchar](20) NULL,
	[email] [varchar](100) NULL,
	[address] [text] NULL,
	[created_at] [datetime] NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[supplier_number] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
ALTER TABLE [dbo].[accounts] ADD  DEFAULT ('Pending') FOR [payment_status]
GO
ALTER TABLE [dbo].[card_transactions] ADD  DEFAULT (getdate()) FOR [transaction_date]
GO
ALTER TABLE [dbo].[employee_salary] ADD  DEFAULT ((0)) FOR [bonus]
GO
ALTER TABLE [dbo].[employee_salary] ADD  DEFAULT ((0)) FOR [deductions]
GO
ALTER TABLE [dbo].[employees] ADD  DEFAULT ('uploads/default.png') FOR [image_url]
GO
ALTER TABLE [dbo].[offline_orders] ADD  DEFAULT (getdate()) FOR [order_date]
GO
ALTER TABLE [dbo].[offline_orders] ADD  DEFAULT (getdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT (getdate()) FOR [order_date]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT ('Pending') FOR [status]
GO
ALTER TABLE [dbo].[shipments] ADD  DEFAULT (getdate()) FOR [shipped_date]
GO
ALTER TABLE [dbo].[shipments] ADD  DEFAULT ('Processing') FOR [status]
GO
ALTER TABLE [dbo].[Suppliers] ADD  DEFAULT (getdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[accounts]  WITH CHECK ADD FOREIGN KEY([customer_id])
REFERENCES [dbo].[customers] ([id])
GO
ALTER TABLE [dbo].[accounts]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO
ALTER TABLE [dbo].[employee_salary]  WITH CHECK ADD FOREIGN KEY([emp_number])
REFERENCES [dbo].[employees] ([emp_number])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[offline_orders]  WITH CHECK ADD FOREIGN KEY([product_id])
REFERENCES [dbo].[products] ([id])
GO
ALTER TABLE [dbo].[order_items]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO
ALTER TABLE [dbo].[order_items]  WITH CHECK ADD FOREIGN KEY([product_id])
REFERENCES [dbo].[products] ([id])
GO
ALTER TABLE [dbo].[orders]  WITH CHECK ADD FOREIGN KEY([customer_id])
REFERENCES [dbo].[customers] ([id])
GO
ALTER TABLE [dbo].[shipments]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO
ALTER TABLE [dbo].[SupplierGoods]  WITH CHECK ADD FOREIGN KEY([supplier_number])
REFERENCES [dbo].[Suppliers] ([supplier_number])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[card_transactions]  WITH CHECK ADD CHECK  (([expiry_month]>=(1) AND [expiry_month]<=(12)))
GO
USE [master]
GO
ALTER DATABASE [TextileShopDB] SET  READ_WRITE 
GO
